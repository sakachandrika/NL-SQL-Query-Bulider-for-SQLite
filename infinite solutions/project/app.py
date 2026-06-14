"""
app.py — NL → SQL Query Builder for SQLite
Run: streamlit run app.py
"""

import os
import uuid
from pathlib import Path

import streamlit as st
=cd
# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NL → SQL Query Builder",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Local imports (after page config) ─────────────────────────────────────────
from utils.schema   import get_schema_string, get_table_stats
from utils.safety   import check_query_safety, SafetyViolation, rate_limiter
from utils.executor import run_query, df_to_csv_bytes
from utils.llm_agent import generate_sql, correct_sql, explain_query
from data.create_db import create_database, DB_PATH

# ── Ensure DB exists ───────────────────────────────────────────────────────────
if not DB_PATH.exists():
    with st.spinner("🛠️ Setting up sample database…"):
        create_database()

DB_PATH_STR = str(DB_PATH)

# ── Session state ──────────────────────────────────────────────────────────────
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())[:8]
if "history" not in st.session_state:
    st.session_state.history = []   # list of {question, sql, rows, time_ms, error}

SESSION_ID = st.session_state.session_id

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Header accent */
    .main-title { font-size: 2.2rem; font-weight: 800; color: #1a1a2e; }
    .subtitle   { color: #6b7280; font-size: 1rem; margin-top: -8px; }

    /* SQL code block */
    .sql-box {
        background: #0f172a;
        color: #e2e8f0;
        padding: 1rem 1.2rem;
        border-radius: 8px;
        font-family: 'JetBrains Mono', 'Courier New', monospace;
        font-size: 0.88rem;
        line-height: 1.6;
        white-space: pre-wrap;
        border-left: 4px solid #6366f1;
    }

    /* Metric cards */
    .metric-row { display: flex; gap: 1rem; margin: 0.8rem 0; flex-wrap: wrap; }
    .metric-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 0.6rem 1rem;
        min-width: 140px;
        text-align: center;
    }
    .metric-card .val { font-size: 1.4rem; font-weight: 700; color: #6366f1; }
    .metric-card .lbl { font-size: 0.75rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; }

    /* Safety warning */
    .safety-warn {
        background: #fef2f2; border: 1px solid #fecaca;
        border-radius: 8px; padding: 0.8rem 1rem; color: #991b1b;
    }

    /* Example chips */
    .example-chip {
        display: inline-block; background: #eef2ff; color: #4338ca;
        padding: 4px 10px; border-radius: 20px; font-size: 0.8rem;
        margin: 3px; cursor: pointer;
    }

    /* Explanation box */
    .explain-box {
        background: #f0fdf4; border-left: 4px solid #22c55e;
        padding: 0.8rem 1rem; border-radius: 0 8px 8px 0;
        color: #166534; font-size: 0.92rem;
    }

    /* Sidebar schema */
    .schema-table {
        font-size: 0.8rem; background: #f8fafc;
        border-radius: 6px; padding: 0.5rem;
        font-family: monospace; white-space: pre;
    }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## ⚙️ Settings")

    api_key = st.text_input(
        "Anthropic API Key",
        value=os.environ.get("ANTHROPIC_API_KEY", ""),
        type="password",
        help="Get yours at console.anthropic.com",
    )

    st.divider()
    st.markdown("## 🗃️ Database Stats")
    try:
        stats = get_table_stats(DB_PATH_STR)
        for table, count in stats.items():
            st.metric(table, f"{count:,} rows")
    except Exception:
        st.info("Database not yet loaded.")

    st.divider()
    st.markdown("## 📋 Schema")
    with st.expander("View full schema", expanded=False):
        try:
            schema_str = get_schema_string(DB_PATH_STR)
            st.code(schema_str, language="sql")
        except Exception as e:
            st.error(str(e))

    st.divider()
    st.markdown("## 🛡️ Safety Info")
    st.caption(
        "✅ Read-only connection  \n"
        "✅ SELECT-only queries  \n"
        "✅ Keyword blocklist  \n"
        "✅ 10 queries/min limit  \n"
        "✅ Full audit logging"
    )

    st.divider()
    st.markdown(f"**Session:** `{SESSION_ID}`")


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN CONTENT
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<p class="main-title">🔍 NL → SQL Query Builder</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Ask questions in plain English — get working SQL back instantly.</p>', unsafe_allow_html=True)

# ── Example questions ──────────────────────────────────────────────────────────
EXAMPLES = [
    "Top 5 products by total revenue in the last 30 days",
    "Total revenue by product category this month",
    "Top 10 customers by number of orders",
    "Which city has the most orders?",
    "Average order value by month for the last 6 months",
    "List all premium customers who ordered in the last 7 days",
    "Products with the most units sold overall",
    "Revenue comparison: completed vs refunded orders",
    "How many new customers signed up each month this year?",
    "Top 3 best-selling products per category",
]

st.markdown("**💡 Example questions — click to use:**")
cols = st.columns(5)
prefill_question = None
for i, example in enumerate(EXAMPLES):
    if cols[i % 5].button(example, key=f"ex_{i}", use_container_width=True):
        prefill_question = example

st.divider()

# ── Query input ────────────────────────────────────────────────────────────────
question = st.text_area(
    "Ask a question about your data (in plain English)",
    value=prefill_question or "",
    height=80,
    placeholder="e.g. What are the top 5 products by total revenue in the last 30 days?",
)

col_run, col_clear = st.columns([1, 6])
run_btn   = col_run.button("▶ Run Query", type="primary", use_container_width=True)
col_clear.button("🗑 Clear History", on_click=lambda: st.session_state.history.clear())

# ── Guard: API key ─────────────────────────────────────────────────────────────
if run_btn:
    if not api_key:
        st.error("⚠️ Please enter your Anthropic API key in the sidebar.")
        st.stop()
    if not question.strip():
        st.warning("Please type a question first.")
        st.stop()

    # ── Rate limit ─────────────────────────────────────────────────────────────
    allowed, remaining = rate_limiter.is_allowed(SESSION_ID)
    if not allowed:
        st.error("🚫 Rate limit reached: max 10 queries per minute. Please wait.")
        st.stop()

    with st.status("🤖 Generating SQL…", expanded=True) as status:
        # 1. Load schema
        st.write("📐 Introspecting database schema…")
        schema_str = get_schema_string(DB_PATH_STR)

        # 2. Generate SQL
        st.write("✍️ Asking Claude to write the SQL…")
        try:
            sql = generate_sql(question, schema_str, api_key=api_key)
        except Exception as e:
            st.error(f"LLM error: {e}")
            st.stop()

        # 3. Safety check
        st.write("🛡️ Running safety checks…")
        try:
            check_query_safety(sql)
        except SafetyViolation as sv:
            status.update(label="🚨 Safety check failed", state="error")
            st.markdown(
                f'<div class="safety-warn">⛔ <strong>Blocked:</strong> {sv}</div>',
                unsafe_allow_html=True,
            )
            st.code(sql, language="sql")
            st.stop()

        status.update(label="✅ SQL generated", state="complete")

    # ── Show the generated SQL BEFORE executing ──────────────────────────────────
    st.markdown("### 📝 Generated SQL")
    st.markdown(f'<div class="sql-box">{sql}</div>', unsafe_allow_html=True)

    # ── Execute (after the SQL has been shown) ────────────────────────────────────
    original_sql = sql
    was_corrected = False
    with st.status("⚡ Executing query…", expanded=True) as exec_status:
        result = run_query(sql, DB_PATH_STR, user_id=SESSION_ID, question=question)

        # Auto-correct if failed
        if not result.success:
            exec_status.write("🔧 Query failed — attempting auto-correction…")
            try:
                sql_fixed = correct_sql(question, sql, result.error, schema_str, api_key=api_key)
                check_query_safety(sql_fixed)
                result = run_query(sql_fixed, DB_PATH_STR, user_id=SESSION_ID, question=question)
                if result.success:
                    sql = sql_fixed
                    was_corrected = True
                    exec_status.write("✅ Auto-correction succeeded! Corrected SQL shown below.")
            except Exception:
                pass   # Show original error below

        exec_status.update(label="✅ Done!", state="complete")

    # If auto-correction changed the SQL, show the corrected version
    if was_corrected:
        st.markdown("### 📝 Corrected SQL (after auto-fix)")
        st.markdown(f'<div class="sql-box">{sql}</div>', unsafe_allow_html=True)

    if result.success:
        # Metrics
        st.markdown(
            f'<div class="metric-row">'
            f'<div class="metric-card"><div class="val">{result.row_count:,}</div><div class="lbl">Rows returned</div></div>'
            f'<div class="metric-card"><div class="val">{result.execution_time_ms:.0f}ms</div><div class="lbl">Execution time</div></div>'
            f'<div class="metric-card"><div class="val">{remaining}</div><div class="lbl">Queries left/min</div></div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # Results table
        st.markdown("### 📊 Results")
        if result.row_count == 0:
            st.info("Query ran successfully but returned no rows.")
        else:
            st.dataframe(result.df, use_container_width=True, height=400)
            st.download_button(
                "⬇️ Download as CSV",
                data=df_to_csv_bytes(result.df),
                file_name="query_results.csv",
                mime="text/csv",
            )

        # Explanation
        with st.expander("💬 What does this query do?", expanded=False):
            with st.spinner("Generating explanation…"):
                try:
                    explanation = explain_query(question, sql, schema_str, api_key=api_key)
                    st.markdown(
                        f'<div class="explain-box">{explanation}</div>',
                        unsafe_allow_html=True,
                    )
                except Exception as e:
                    st.caption(f"Could not generate explanation: {e}")

        # Save to history
        st.session_state.history.insert(0, {
            "question": question, "sql": sql,
            "rows": result.row_count, "time_ms": result.execution_time_ms,
            "error": None,
        })

    else:
        st.error(f"❌ Query execution failed:\n```\n{result.error}\n```")
        st.session_state.history.insert(0, {
            "question": question, "sql": sql,
            "rows": 0, "time_ms": result.execution_time_ms,
            "error": result.error,
        })

# ── Query history ──────────────────────────────────────────────────────────────
if st.session_state.history:
    st.divider()
    st.markdown("### 🕘 Query History (this session)")
    for i, entry in enumerate(st.session_state.history[:10]):
        icon = "✅" if not entry["error"] else "❌"
        with st.expander(f"{icon}  {entry['question'][:80]}…" if len(entry["question"]) > 80 else f"{icon}  {entry['question']}"):
            st.code(entry["sql"], language="sql")
            if entry["error"]:
                st.error(entry["error"])
            else:
                st.caption(f"Returned **{entry['rows']:,} rows** in **{entry['time_ms']:.0f}ms**")
            # Re-run button
            if st.button("↩️ Re-run this question", key=f"rerun_{i}"):
                st.session_state["_rerun_question"] = entry["question"]
                st.rerun()