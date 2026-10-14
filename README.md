# ClarifySQL

### Ask business questions. Get data-backed answers.

ClarifySQL is a Python and Streamlit business analytics application that lets users explore sample retail sales data by asking supported questions in natural language. It uses predefined SQL templates and a local SQLite database. It does not currently connect to an external AI API or generate unrestricted SQL using an LLM.

## Features

- Business overview dashboard
- Natural-language questions in English, Hinglish, and selected Hindi patterns
- Revenue and profit analysis
- Product and category performance
- Monthly revenue and month-over-month comparison
- Missing calendar months are shown as unavailable; comparisons that depend on missing-month data are not calculated.
- Product revenue decline analysis across the two latest available months
- Completed and cancelled order analysis
- Multiple-question handling for supported patterns
- Read-only SQL validation and SQLite safeguards
- Automated unit tests

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
|-- app.py
|-- core/
|   |-- analytics.py
|   |-- database.py
|   `-- query_engine.py
|-- data/                 # Local database; excluded from Git
|-- tests/
|   `-- test_query_engine.py
|-- ui/
|   `-- styles.py
|-- requirements.txt
|-- .gitignore
`-- README.md
```

## Setup on Windows

### 1. Get the project

Clone the repository or download its source code, then open PowerShell in the project directory.

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

This creates the `data` directory and initializes the SQLite tables and reproducible sample data when the database is empty. The database file is excluded from Git, so each fresh clone should initialize its own sample database.

**Important:** The initializer does not reset an existing database. It skips generating sales when orders already exist.

### 5. Run the application

```powershell
python -m streamlit run app.py --server.port 8507
```

Open `http://localhost:8507` in your browser.

## Example Questions

### Revenue and profit

- What is the total revenue?
- What is the total profit?
- Total profit kitna hai?

### Products

- Which product has the highest revenue?
- Which product has the highest profit?
- Show top 5 products.
- Which products contributed most to the revenue decline?
- Which product is best?  
  The application should ask whether 'best' means revenue, profit, or units sold.

### Trends and categories

- Show monthly revenue.
- Compare monthly revenue.
- Compare revenue by category.

### Orders

- How many orders were cancelled?

Question recognition depends on supported patterns. Clarification and language coverage are limited; the application may not understand every possible question.

## SQL Safety

ClarifySQL validates its predefined SQL queries before execution.

- SQL is parsed using SQLGlot.
- Only one read-only `SELECT` statement is accepted.
- References are restricted to approved database tables.
- SQLite is opened in read-only mode for analytics queries.
- SQLite query-only mode and an authorizer provide additional restrictions.

These safeguards reduce the risk of unintended database changes but do not guarantee protection against every possible security vulnerability.

## Running Tests

From the project root, activate the virtual environment and run:

```powershell
python -m unittest discover -s tests -v
```

To check Python syntax:

```powershell
python -m py_compile app.py core\analytics.py core\database.py core\query_engine.py ui\styles.py tests\test_query_engine.py
```

## Sample Database

The project includes a reproducible sample-data initializer in `core/database.py`. It creates a local SQLite database with products, orders, and order items. Analytics results depend on the data in the local database.

The database file is excluded from Git. Do not commit private or production data.

## Optional AI SQL Configuration

The deterministic query engine works without an external AI service. To enable
the optional AI SQL fallback, configure an API key for an OpenAI-compatible
chat-completions endpoint in the PowerShell session used to run ClarifySQL:

```powershell
$env:CLARIFYSQL_AI_API_KEY = "your-api-key"
# Optional overrides:
$env:CLARIFYSQL_AI_BASE_URL = "https://api.openai.com/v1"
$env:CLARIFYSQL_AI_MODEL = "gpt-4o-mini"
python -m streamlit run app.py --server.port 8507
```

Do not commit API keys or paste them into source files. The fallback validates
generated SQL with the application's read-only SQL validator before execution.
AI output can still be incorrect, and schema access or SQL validation does not
guarantee that an answer is business-correct. Without an API key, this optional
fallback remains inactive.

## Current Limitations

- Deterministic question patterns and SQL templates work without an API key. An optional OpenAI-compatible AI SQL fallback is available when configured.
- Only supported question patterns are interpreted.
- The sample dataset covers January through June 2026.
- Results depend on the local database contents.
- Automated tests do not cover every UI interaction.
- The application is intended as a local demonstration, not a production multi-user analytics service.

## Future Improvements

- Broaden natural-language question coverage and ambiguity clarification
- Add UI and end-to-end tests
- Expand business analytics
- Improve setup automation and documentation

## License

No open-source license has been specified. Add a `LICENSE` file before publishing if you want to grant users explicit open-source permissions.


## Evaluation

ClarifySQL includes a small labeled dataset for evaluating its ambiguity detector.

Run the evaluation from the project root:

```powershell
& ".\.venv\Scripts\python.exe" ".\evaluation\evaluate_ambiguity.py"
```

The runner compares the detector with a baseline that never asks for clarification.
It reports accuracy, precision, recall, F1, and confusion-matrix counts.
Detailed output is written to `evaluation/evaluation_results.json`.

These results measure agreement with the included sample labels only. They do
not establish SQL-answer accuracy or guarantee performance on unseen questions.
Review and expand the dataset as supported business intents evolve.

## Optional AI configuration

AI SQL generation is optional. Without `CLARIFYSQL_AI_API_KEY`, ClarifySQL
continues to use its deterministic query handling.

Set the API key in your local PowerShell session without writing it into source
files:

```powershell
$env:CLARIFYSQL_AI_API_KEY = "your-real-api-key"
$env:CLARIFYSQL_AI_BASE_URL = "https://api.openai.com/v1"
$env:CLARIFYSQL_AI_MODEL = "gpt-4o-mini"
```

Keep the key private and never commit it to Git.
