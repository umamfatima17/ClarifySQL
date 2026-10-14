"""Optional schema-aware SQL generation using an OpenAI-compatible API."""

import json
import os
import urllib.error
import urllib.request

from core.schema_inspector import get_database_schema


def generate_sql(question, previous_sql=None, error_message=None):
    """Generate SQL or attempt a targeted correction when prior SQL failed."""
    api_key = os.getenv("CLARIFYSQL_AI_API_KEY", "").strip()
    if not api_key:
        return None

    base_url = os.getenv(
        "CLARIFYSQL_AI_BASE_URL", "https://api.openai.com/v1"
    ).strip().rstrip("/")
    model = os.getenv("CLARIFYSQL_AI_MODEL", "gpt-4o-mini").strip()

    if not base_url.startswith(("https://", "http://")):
        raise RuntimeError("The AI API base URL must use HTTP or HTTPS.")

    schema_text = json.dumps(
        get_database_schema(include_sample_values=True),
        ensure_ascii=False,
        indent=2,
    )

    messages = [
        {
            "role": "system",
            "content": (
                "You generate SQLite queries for a business analytics app. "
                "Return only one SQL SELECT statement, without Markdown. "
                "Use only tables and columns present in the supplied schema. "
                "Use the supplied sample values when relevant to filters. "
                "Never generate INSERT, UPDATE, DELETE, DROP, PRAGMA, ATTACH, "
                "or any other non-SELECT statement. Do not guess missing columns. "
                "Use explicit JOIN conditions when joining tables. "
                "For detail-row queries, use LIMIT 200. "
                "If the question cannot be answered from the schema, return "
                "a SELECT query against an available table that returns no rows."
            ),
        },
        {
            "role": "user",
            "content": (
                "Database schema and bounded sample values:\n"
                + schema_text
                + "\n\nBusiness question:\n"
                + str(question)
            ),
        },
    ]

    if previous_sql or error_message:
        messages.append(
            {
                "role": "user",
                "content": (
                    "The previous SQL attempt failed. Correct it while answering "
                    "the same business question. Do not repeat the same failure. "
                    "Use only the supplied schema and return one SELECT statement.\n"
                    "Previous SQL:\n"
                    + str(previous_sql or "(not available)")[:6000]
                    + "\nFailure details:\n"
                    + str(error_message or "Unknown failure")[:1500]
                ),
            }
        )

    payload = {
        "model": model,
        "temperature": 0,
        "messages": messages,
    }

    request = urllib.request.Request(
        base_url + "/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": "Bearer " + api_key,
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            result = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError("The AI SQL service could not be reached.") from exc

    try:
        content = result["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("The AI service returned an unexpected response.") from exc

    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("The AI service returned empty SQL.")

    sql = content.strip()

    if sql.startswith("```"):
        sql = sql.strip("`").strip()
        if sql.lower().startswith("sql"):
            sql = sql[3:].strip()

    return sql
