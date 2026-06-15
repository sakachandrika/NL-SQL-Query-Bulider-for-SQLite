"""
utils/executor.py — Read-only query execution + audit logging
"""

import csv
import io
import time
import logging
from datetime import datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, event, text
from sqlalchemy.exc import SQLAlchemyError

# ── Audit logger ──────────────────────────────────────────────────────────────
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

audit_logger = logging.getLogger("nl2sql.audit")
audit_logger.setLevel(logging.INFO)

if not audit_logger.handlers:
    fh = logging.FileHandler(LOG_DIR / "query_audit.log")
    fh.setFormatter(
        logging.Formatter("%(asctime)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    )
    audit_logger.addHandler(fh)


def _make_readonly_engine(db_path: str):
    """Create a SQLAlchemy engine that opens the DB in immutable read-only mode."""
    uri = f"sqlite:///file:{db_path}?mode=ro&uri=true"
    engine = create_engine(
        uri,
        connect_args={"check_same_thread": False},
    )

    # Belt-and-suspenders: block any non-SELECT at the engine level
    @event.listens_for(engine, "before_execute")
    def _block_writes(conn, clauseelement, multiparams, params, execution_options):
        sql_str = str(clauseelement).strip().upper()
        # Allow EXPLAIN and SELECT
        if not (sql_str.startswith("SELECT") or sql_str.startswith("EXPLAIN")):
            raise PermissionError(f"Write operations are blocked. Received: {sql_str[:40]}")

    return engine


class QueryResult:
    def __init__(
        self,
        df: pd.DataFrame | None,
        execution_time_ms: float,
        row_count: int,
        error: str | None = None,
    ):
        self.df               = df
        self.execution_time_ms = execution_time_ms
        self.row_count        = row_count
        self.error            = error

    @property
    def success(self) -> bool:
        return self.error is None


def run_query(
    sql: str,
    db_path: str,
    user_id: str = "anonymous",
    question: str = "",
) -> QueryResult:
    """
    Execute a SELECT query and return a QueryResult.
    Logs every attempt to the audit log.
    """
    engine = _make_readonly_engine(db_path)
    start  = time.perf_counter()

    try:
        # Validate with EXPLAIN first
        with engine.connect() as conn:
            conn.execute(text(f"EXPLAIN {sql}"))

        # Run the actual query
        with engine.connect() as conn:
            df = pd.read_sql_query(sql=text(sql), con=conn)

        elapsed_ms = (time.perf_counter() - start) * 1000
        row_count  = len(df)

        audit_logger.info(
            f"user={user_id} | status=SUCCESS | rows={row_count} | "
            f"time={elapsed_ms:.1f}ms | question={repr(question)} | sql={repr(sql)}"
        )

        return QueryResult(df=df, execution_time_ms=elapsed_ms, row_count=row_count)

    except SQLAlchemyError as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000
        error_msg  = str(exc.orig) if hasattr(exc, "orig") else str(exc)

        audit_logger.info(
            f"user={user_id} | status=ERROR | time={elapsed_ms:.1f}ms | "
            f"question={repr(question)} | sql={repr(sql)} | error={repr(error_msg)}"
        )

        return QueryResult(df=None, execution_time_ms=elapsed_ms, row_count=0, error=error_msg)

    except Exception as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000
        audit_logger.info(
            f"user={user_id} | status=BLOCKED | time={elapsed_ms:.1f}ms | "
            f"question={repr(question)} | sql={repr(sql)} | error={repr(str(exc))}"
        )
        return QueryResult(df=None, execution_time_ms=elapsed_ms, row_count=0, error=str(exc))


def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue().encode("utf-8")
