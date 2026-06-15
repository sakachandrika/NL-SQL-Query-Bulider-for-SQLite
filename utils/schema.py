"""
utils/schema.py — SQLAlchemy schema introspection
Returns a formatted CREATE TABLE string to inject into LLM prompts.
"""

from sqlalchemy import create_engine, inspect, text


def get_schema_string(db_path: str) -> str:
    """
    Connect to a SQLite database and return a CREATE TABLE schema
    string for all user tables, including foreign-key relationships.
    """
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    inspector = inspect(engine)
    lines: list[str] = []

    for table_name in inspector.get_table_names():
        columns     = inspector.get_columns(table_name)
        pk_info     = inspector.get_pk_constraint(table_name)
        pk_cols     = set(pk_info.get("constrained_columns", []))
        foreign_keys = inspector.get_foreign_keys(table_name)

        lines.append(f"CREATE TABLE {table_name} (")
        col_defs = []
        for col in columns:
            col_type = str(col["type"])
            nullable = "" if col.get("nullable", True) else " NOT NULL"
            pk_flag  = " PRIMARY KEY" if col["name"] in pk_cols else ""
            default  = f" DEFAULT {col['default']}" if col.get("default") is not None else ""
            col_defs.append(f"    {col['name']}  {col_type}{pk_flag}{nullable}{default}")

        # FK constraints
        for fk in foreign_keys:
            for local_col, ref_col in zip(fk["constrained_columns"], fk["referred_columns"]):
                col_defs.append(
                    f"    FOREIGN KEY ({local_col}) REFERENCES {fk['referred_table']}({ref_col})"
                )

        lines.append(",\n".join(col_defs))
        lines.append(");\n")

    return "\n".join(lines)


def get_table_stats(db_path: str) -> dict[str, int]:
    """Return row counts for every table (for sidebar display)."""
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    inspector = inspect(engine)
    stats: dict[str, int] = {}
    with engine.connect() as conn:
        for table in inspector.get_table_names():
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
            stats[table] = result.scalar()
    return stats
