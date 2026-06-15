"""
utils/llm_agent.py — NL → SQL generation via a local Ollama model
No API key required. Talks to the Ollama server running on localhost:11434.
"""

import json
import urllib.request
import urllib.error

# ── Configuration ──────────────────────────────────────────────────────────────
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "qwen2.5-coder:7b"   # change to qwen2.5-coder:3b for lower-spec machines


def _chat(system: str, user: str, max_tokens: int = 512) -> str:
    """
    Send a chat request to the local Ollama server and return the text reply.
    Raises a clear error if Ollama isn't running.
    """
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
        "stream": False,
        "options": {
            "temperature": 0.0,        # deterministic SQL
            "num_predict": max_tokens,
        },
    }

    data = json.dumps(payload).encode("utf-8")
    req  = urllib.request.Request(
        OLLAMA_URL,
        data=data,
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        return body["message"]["content"].strip()
    except urllib.error.URLError as e:
        raise RuntimeError(
            "Could not reach Ollama at localhost:11434. "
            "Make sure Ollama is installed and running, and that you've pulled "
            f"the model with:  ollama pull {MODEL_NAME}\n\nDetails: {e}"
        ) from e


def _clean_sql(text: str) -> str:
    """Strip markdown fences and stray prefixes the model might add."""
    sql = text.strip()
    if sql.startswith("```"):
        lines = sql.splitlines()
        lines = [ln for ln in lines if not ln.strip().startswith("```")]
        sql = "\n".join(lines).strip()
    if sql.lower().startswith("sql"):
        sql = sql[3:].strip()
    return sql.strip("`").strip()


# ── Prompts ─────────────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are an expert SQLite SQL assistant.

You are given a database schema below. Your ONLY job is to convert the user's natural-language question into a valid, read-only SQLite SELECT query.

Rules:
1. Return ONLY the raw SQL query — no markdown, no backticks, no explanation, no preamble.
2. Use only SELECT statements. Never use DROP, DELETE, UPDATE, INSERT, or any DDL/DML.
3. Always use table aliases when joining multiple tables.
4. Use DATE('now') for current date comparisons, not hardcoded dates.
5. Use strftime() for date arithmetic (e.g. strftime('%Y-%m', order_date) for month grouping).
6. Limit results to 100 rows unless the question asks for all records.
7. Use meaningful column aliases in the output (e.g. total_revenue instead of SUM(total_amount)).
8. If the question is ambiguous, make a reasonable assumption.

Database Schema:
{schema}"""

CORRECTION_SYSTEM_PROMPT = """You are an expert SQLite SQL debugger.

The following SQL query was generated for a user's question but failed with an error.
Your job is to fix the query and return ONLY the corrected SQL — no explanation, no backticks, no preamble.

Rules:
1. Return ONLY the raw corrected SQL query.
2. Only SELECT queries are allowed.
3. Use DATE('now') for current date, strftime() for date formatting.

Database Schema:
{schema}"""


# ── Public API (same signatures as before; api_key/model args ignored) ──────────
def generate_sql(question: str, schema: str, api_key: str | None = None, model: str | None = None) -> str:
    """Generate SQL from a natural-language question."""
    system = SYSTEM_PROMPT.format(schema=schema)
    raw = _chat(system, question)
    return _clean_sql(raw)


def correct_sql(question: str, bad_sql: str, error_message: str, schema: str,
                api_key: str | None = None, model: str | None = None) -> str:
    """Auto-correct a failing SQL query."""
    system = CORRECTION_SYSTEM_PROMPT.format(schema=schema)
    user = (
        f"Original question: {question}\n\n"
        f"Failing SQL:\n{bad_sql}\n\n"
        f"Error message:\n{error_message}"
    )
    raw = _chat(system, user)
    return _clean_sql(raw)


def explain_query(question: str, sql: str, schema: str,
                  api_key: str | None = None, model: str | None = None) -> str:
    """Return a plain-English explanation of what the SQL query does."""
    system = "You are a helpful data analyst who explains SQL queries in simple terms for non-technical people."
    user = (
        f"The user asked: '{question}'\n\n"
        f"The following SQL query was generated:\n{sql}\n\n"
        f"Explain in 2-3 plain English sentences what this query does, "
        f"mentioning which tables it uses and what it calculates. "
        f"Do not repeat the SQL."
    )
    return _chat(system, user, max_tokens=256).strip()
