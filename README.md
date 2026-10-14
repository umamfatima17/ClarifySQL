# ClarifySQL

**Turn business questions into validated, data-backed answers.**

ClarifySQL is a Streamlit-based business analytics application that lets users explore retail sales data through natural-language questions. It combines deterministic query handling, clarification for ambiguous questions, SQL validation, and a local SQLite database.

The project is designed as a local demonstration of Python, SQL, analytics, and responsible query execution.

## Features

- **Business dashboard:** Explore available retail sales data and analytics.
- **Natural-language queries:** Ask supported business questions in English, Hinglish, and selected Hindi patterns.
- **Clarification-first workflow:** Resolve ambiguous questions before running a query.
- **Revenue and profit analytics:** Explore sales performance, products, categories, and monthly trends.
- **Monthly comparisons:** Compare revenue across months and analyze supported changes.
- **Order analysis:** Explore supported completed and cancelled order questions.
- **Saved clarification sessions:** Store, resume, and review pending clarification conversations.
- **SQL safety:** Validate queries before execution and restrict analytics queries to read-only operations.
- **Optional AI SQL fallback:** Enable an OpenAI-compatible chat-completions endpoint with an API key.
- **Evaluation and tests:** Run ambiguity-detection evaluation and automated unit tests.

Question recognition is based on supported patterns and available data. The application does not understand every possible business question.

## Technology Stack

- Python
- Streamlit
- SQLite
- Pandas
- Plotly
- SQLGlot
- Python `unittest`

## Project Structure

```text
ClarifySQL/
??? app.py
??? core/
?   ??? ai_sql_generator.py
?   ??? analytics.py
?   ??? clarification_engine.py
?   ??? database.py
?   ??? query_engine.py
?   ??? schema_inspector.py
?   ??? session_store.py
??? data/                    # Local SQLite database; excluded from Git
??? evaluation/
?   ??? evaluate_ambiguity.py
?   ??? evaluation_cases.json
?   ??? evaluation_results.json
??? tests/
??? ui/
?   ??? styles.py
??? .env.example
??? .gitignore
??? requirements.txt
??? README.md
```

## Getting Started on Windows

### 1. Clone the repository

```powershell
git clone https://github.com/umamfatima17/ClarifySQL.git
cd ClarifySQL
```

### 2. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 4. Initialize the sample database

```powershell
python -m core.database
```

This initializes the local SQLite database and sample retail data when initialization is needed. It does not reset an existing populated database.

### 5. Start the application

```powershell
python -m streamlit run app.py --server.port 8507
```

Open [http://localhost:8507](http://localhost:8507) in your browser.

## Example Questions

Try questions such as:

- What is the total revenue?
- What is the total profit?
- Total profit kitna hai?
- Which product has the highest revenue?
- Which product has the highest profit?
- Show top 5 products.
- Show monthly revenue.
- Compare March 2026 revenue with April 2026.
- How many orders were cancelled?
- Which product is the best?

For ambiguous questions such as "Which product is the best?", ClarifySQL can ask which metric to use, such as revenue, profit, or units sold. Available results depend on the database contents and supported query patterns.

## Clarification Sessions

Clarification conversations can be saved in the local SQLite database. Pending sessions can be resumed through the application, allowing users to continue answering clarification questions rather than starting over.

The session store uses separate tables for clarification sessions and their messages. These tables are initialized by the application.

## SQL Safety

ClarifySQL uses SQLGlot and application-level checks to validate analytics queries before execution.

The safeguards include:

- Restricting accepted SQL to a single read-only `SELECT` statement.
- Restricting references to approved database tables.
- Opening analytics connections in read-only mode.
- Applying SQLite query-only mode and an authorizer.

These measures reduce the risk of unintended database modifications. They do not guarantee protection against every possible security vulnerability or incorrect business interpretation.

## Optional AI SQL Fallback

The deterministic query engine works without an external AI API. An optional AI SQL fallback can be configured with an OpenAI-compatible chat-completions endpoint.

Set these variables in the PowerShell session before starting the application:

```powershell
$env:CLARIFYSQL_AI_API_KEY = "your-api-key"

# Optional overrides
$env:CLARIFYSQL_AI_BASE_URL = "https://api.openai.com/v1"
$env:CLARIFYSQL_AI_MODEL = "gpt-4o-mini"

python -m streamlit run app.py --server.port 8507
```

Use your own valid API key. Never commit credentials or paste them into source code. Keep `.env` and other secret files out of Git.

Generated SQL must still pass the application's validation before execution. AI-generated output may be incorrect, and SQL validation alone cannot guarantee that an answer is business-correct. Without an API key, the optional fallback remains inactive.

## Running Tests

Run the full automated test suite from the project root:

```powershell
python -m unittest discover -s tests -v
```

Check Python syntax:

```powershell
python -m compileall -q app.py core tests
```

## Ambiguity Evaluation

The project includes a small labeled dataset for evaluating its ambiguity detector.

Run the evaluation:

```powershell
python .\evaluation\evaluate_ambiguity.py
```

The evaluation reports metrics such as accuracy, precision, recall, F1, and confusion-matrix counts against a simple baseline. Results are based only on the included examples; they do not establish general performance on unseen questions or SQL-answer accuracy.

## Data and Privacy

The sample database is local and excluded from Git. Initialize it separately after cloning. Do not commit private, production, or otherwise sensitive data.

The `.venv` directory, Python caches, local database files, and local credentials should remain outside version control.

## Current Limitations

- Only supported natural-language patterns and intents are handled.
- The sample dataset covers a limited period and business schema.
- AI SQL generation requires separately configured API access.
- The evaluation dataset is small and manually labeled.
- Automated tests do not cover every possible UI interaction.
- The application is intended as a local project demonstration, not a production multi-user analytics service.

## License

No open-source license has been specified. Add a `LICENSE` file if you intend to grant others explicit permission to use, modify, or distribute this project.
