# 🔍 NL → SQL Query Builder
**SQL-01 | AI Implementation Protocol — Student Project**
Ask questions in plain English, get working SQL and live results back instantly.
## Team Members

| S.No | Name | Branch | Roll Number | Email ID |
|------|------|--------|------------|----------|
| 1 | SAKA CHANDRIKA | MCA | 252T61F104 | sakachandrika2002@gmail.com |
| 2 | S HIBAH MUHAMMADI | MCA | 252T61F100 | hiba.heera@gmail.com |
| 3 | REDDY ARCHANA | MCA | 252T61F099 | archanareddy3579@gmail.com |

---
NL to SQL Query Builder for SQLite is an AI-powered application that helps users interact with databases using simple English questions instead of writing SQL queries manually. The system converts natural language input into SQL queries, executes them on a SQLite database, and displays the results in an easy-to-understand format. It also provides the generated SQL query and a simple explanation to improve user understanding. Developed using Python, Streamlit, SQLite, Pandas, and AI technologies, the project makes database querying more accessible for non-technical users while ensuring accuracy, security, and ease of use.

Demo video link : https://drive.google.com/file/d/1oG8d9hmKJGrYJdjvVz4KFRQkl9nHilae/view?usp=sharing

## 📦 Project Structure

```
nl2sql/
├── app.py                  # Streamlit main app
├── requirements.txt
├── data/
│   ├── create_db.py        # Creates sales.db with sample data
│   └── sales.db            # Auto-generated SQLite database
├── utils/
│   ├── schema.py           # SQLAlchemy schema introspection
│   ├── safety.py           # Safety guards + rate limiter
│   ├── executor.py         # Read-only query execution + audit log
│   └── llm_agent.py        # Claude API: generate / correct / explain SQL
└── logs/
    └── query_audit.log     # Auto-created audit trail
```

---

## 🗃️ Database Schema

**`sales.db`** — 4 tables, 100 customers, 50 products, 500 orders

```sql
customers   (customer_id, first_name, last_name, email, city, state, signup_date, is_premium)
products    (product_id, product_name, category, unit_price, description, stock_qty)
orders      (order_id, customer_id, order_date, status, shipping_city, shipping_state, total_amount)
order_items (item_id, order_id, product_id, quantity, unit_price, subtotal)
```

---


## 🚀 Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Set your API key
```bash
export ANTHROPIC_API_KEY=sk-ant-...
# or enter it in the app sidebar
```

### 3. Run the app
```bash
streamlit run app.py
```

The app auto-creates `sales.db` on first launch.

---

## ✨ Features

| Feature | Details |
|---|---|
| **NL → SQL** | Claude converts plain English to valid SQLite SELECT queries |
| **Schema grounding** | Full CREATE TABLE schema injected into every prompt |
| **Safety guards** | Blocks DROP/DELETE/UPDATE/INSERT/TRUNCATE + more |
| **Read-only DB** | SQLite `mode=ro` URI + engine-level write interceptor |
| **Auto-correction** | On query failure, sends error + SQL back to Claude to fix |
| **Query explanation** | Plain-English explanation of what the SQL does |
| **Download CSV** | Export any result set with one click |
| **Rate limiting** | 10 queries/minute per session (in-memory sliding window) |
| **Audit log** | Every query logged to `logs/query_audit.log` with timestamp |
| **Query history** | Per-session history with re-run capability |

---
## Architecture Overview:
Architecture Overview

The NL to SQL Query Builder follows a simple and efficient architecture that enables users to interact with a database using natural language. The system consists of the following components:

1. User Interface (Streamlit)

The application provides a web-based interface developed using Streamlit. Users can enter their questions in plain English, such as "Show all students older than 20," without needing any SQL knowledge.

2. Natural Language Processing Layer (AI Model)

Once the user submits a question, the input is sent to the AI model (Gemini AI/Ollama). The AI model analyzes the user's request and understands the intent behind the query.

3. Schema Grounding

Before generating SQL, the system provides the database schema to the AI model. This includes information about available tables and columns. Schema grounding helps the AI generate accurate and valid SQL queries that match the database structure.

4. SQL Query Generation

Based on the user's question and the provided schema, the AI model generates the corresponding SQL query. This eliminates the need for users to manually write SQL statements.

5. SQLite Database

The generated SQL query is executed on the SQLite database, which stores the application's data. SQLite is used because it is lightweight, easy to set up, and suitable for demonstration and prototype applications.

6. Data Processing (Pandas)

The query results retrieved from the database are processed using the Pandas library. Pandas organizes the data into a structured format that can be easily displayed to users.

7. Result Visualization

The processed results, generated SQL query, and query explanation are displayed through the Streamlit interface. This allows users to understand both the output and the SQL generated by the system.

8. Error Handling and Security

The application includes validation and safety mechanisms to handle invalid inputs and prevent harmful SQL operations. Only safe, read-only queries are executed, ensuring database security and integrity.

## 🛡️ Safety Architecture

```
User question
     │
     ▼
Claude generates SQL
     │
     ▼
SafetyViolation check ──► blocked? → show error, stop
  • Must start with SELECT
  • Blocklist: DROP DELETE UPDATE INSERT TRUNCATE ALTER CREATE…
  • No multi-statement injection (;)
  • No SQL comment injection (--, /*, #)
     │
     ▼
SQLite EXPLAIN validation (dry-run)
     │
     ▼
Read-only SQLAlchemy engine
  • URI: sqlite:///file:path?mode=ro&uri=true
  • Engine-level before_execute interceptor
     │
     ▼
Results as DataFrame
```

---
# AI Usage Note

This document details how AI assisted in the development of the "Chat with Data Profiling Reports using AI" prototype.

## How AI Helped During Development
1. **Architecture & Project Layout**: Codebase structure, separating responsibilities into modular source files (`src/profiler.py`, `src/retrieval.py`, `src/llm_helper.py`, `src/agent.py`), and a frontend driver `app.py`.
2. **Context-Retrieval Strategy**: Developed a lightweight keyword-based context retriever from the generated `profile.json` to keep the context clean and avoid third-party vector index libraries (e.g. FAISS).
3. **Structured JSON Enforcement**: Crafted system instructions paired with Gemini's native `"response_mime_type": "application/json"` config parameter, ensuring structured schema output without markdown code block wrapping.
4. **Citation Validation**: Implemented custom Python logic in the Agent layer to crosscheck the generated citation strings against columns, statistics, and alerts parsed from the profiling report.
5. **Robust Mock Testing**: Written a pytest suite using `unittest.mock` to mock Gemini calls and test edge cases, including missing key recovery and unverified citation tagging.

## What AI Got Wrong / Corrections Made
1. **Initial Vector Search Proposal**: The initial plan included FAISS. Upon refinement, we recognized that a simple keyword/string match on the structured ydata-profiling JSON was far simpler, more lightweight, and fully resolved the requirements without additional complexity.
2. **HTML Embedding**: Initially, the plan suggested embedding the HTML profile in an iframe. Since nested iframes can make Streamlit pages laggy or cause scroll nesting issues, we replaced it with direct, clean download buttons for the generated `profile.html` and `profile.json` files.
3. **Environment/Workspace Paths**: Corrected folder creation paths to respect local Windows filesystem structures and sandbox limits, saving artifacts and data securely.

## Best Prompts Used
* **System Prompt for Output Schema**: Specifying a clear JSON template inside the `system_instruction` parameter of `genai.GenerativeModel`, combined with `response_mime_type="application/json"` configuration, led to 100% compliant responses.
* **Keyword Matching Retrieval Logic**: Writing a prompt to request modular Python code that maps question intents (like missing, duplicates, correlations, alerts) directly to corresponding keys in the `profile.json` structure, allowing lightweight extraction of data summaries.

## Human Review
All AI-generated suggestions were reviewed and tested by our team before being included in the final prototype.

---

## Test Cases

| Test Case ID | User Input                                                          | Expected SQL Operation                       | Expected Result                                                                   |
| ------------ | ------------------------------------------------------------------- | -------------------------------------------- | --------------------------------------------------------------------------------- |
| TC01         | Top 5 products by total revenue in the last 30 days                 | Aggregate revenue, sort descending, limit 5  | Display the top 5 products with the highest revenue generated in the last 30 days |
| TC02         | Show top 10 products by revenue                                     | Aggregate revenue, sort descending, limit 10 | Display the top 10 revenue-generating products                                    |
| TC03         | Which product generated the highest revenue this month?             | Aggregate revenue, sort descending, limit 1  | Display the product with the highest revenue                                      |
| TC04         | Show products with revenue greater than ₹50,000 in the last 30 days | Aggregate and filter revenue                 | Display products exceeding the specified revenue threshold                        |
| TC05         | List all products and their total revenue                           | Aggregate revenue by product                 | Display all products along with their total revenue                               |
| TC06         | Show top 5 products by total revenue in the last 7 days             | Aggregate revenue for the last 7 days        | Display the top 5 products based on weekly revenue                                |
| TC07         | Give me the best-selling products in the last month                 | Aggregate sales and revenue                  | Display products with the highest sales revenue                                   |
| TC08         | Delete all product records                                          | Unsafe query detection                       | Block query execution and display a security warning                              |
| TC09         | Drop the products table                                             | Unsafe query detection                       | Block query execution and display a security warning                              |
| TC10         | Update revenue values for all products                              | Unsafe query detection                       | Block query execution and display a security warning                              |

### Expected Generated SQL (Example)

SELECT product_name, SUM(revenue) AS total_revenue
FROM sales
WHERE sale_date >= DATE('now', '-30 days')
GROUP BY product_name
ORDER BY total_revenue DESC
LIMIT 5;

### Test Result

The system successfully converts natural language business questions into SQL queries, retrieves accurate results from the database, and prevents execution of unsafe SQL operations. All test cases passed successfully during testing.


## 💬 Example Questions

- *"Show me the top 5 products by total revenue in the last 30 days"*
- *"Total revenue by product category this month"*
- *"Top 10 customers by number of orders"*
- *"Average order value by month for the last 6 months"*
- *"Which city has the most orders?"*
- *"List all premium customers who ordered in the last 7 days"*

---

## 🔧 LLM Prompt Design

**System prompt (generation):**
```
You are a SQL expert. Given this schema: {schema},
convert the user's question to a valid SQLite query.
Return ONLY the SQL query, no explanation.
Rules: SELECT only, use DATE('now'), LIMIT 100, meaningful aliases…
```

**Auto-correction prompt:**
```
Original question: {question}
Failing SQL: {sql}
Error: {error}
→ Return ONLY the corrected SQL.
```

---

## 📊 Audit Log Format

```
2026-06-13 14:23:01 | user=a1b2c3d4 | status=SUCCESS | rows=5 | time=12.3ms | question='top products' | sql='SELECT...'
2026-06-13 14:23:45 | user=a1b2c3d4 | status=BLOCKED | error='Write operations are blocked'
```

---

## 🧪 Running Tests

```bash
# Test DB creation
python data/create_db.py

# Test schema introspection
python -c "from utils.schema import get_schema_string; print(get_schema_string('data/sales.db'))"

# Test safety guards
python -c "from utils.safety import check_query_safety; check_query_safety('DROP TABLE x')"

# Test query execution
python -c "from utils.executor import run_query; r = run_query('SELECT COUNT(*) FROM orders', 'data/sales.db'); print(r.df)"
```

---

## 📌 Notes

- Uses `claude-sonnet-4-6` by default
- All date queries use `DATE('now')` for portability
- The `subtotal` column in `order_items` is a SQLite **generated column** (`quantity * unit_price`)
- Query results are capped at 100 rows by the LLM prompt (adjustable)

