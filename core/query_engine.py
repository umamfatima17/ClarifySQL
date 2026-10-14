
import re
import calendar
from datetime import date, timedelta
import sqlite3

import sqlglot
from sqlglot import exp

from core.database import DATABASE_PATH


ALLOWED_TABLES = {"products", "orders", "order_items"}

# These templates are written by us, not supplied directly by users.
# Every query is restricted to reading the sample database.
QUERY_TEMPLATES = {
    "highest_revenue_product": """
        SELECT
            p.product_name AS product_name,
            ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue
        FROM order_items oi
        JOIN orders o ON o.order_id = oi.order_id
        JOIN products p ON p.product_id = oi.product_id
        WHERE o.status = 'completed'
        GROUP BY p.product_id, p.product_name
        ORDER BY revenue DESC
        LIMIT 1
    """,
    "monthly_revenue": """
        WITH RECURSIVE calendar_months(month) AS (
            SELECT MIN(strftime('%Y-%m', o.order_date))
            FROM orders o
            WHERE o.status = 'completed'
              AND EXISTS (
                  SELECT 1
                  FROM order_items i
                  WHERE i.order_id = o.order_id
              )
            HAVING MIN(strftime('%Y-%m', o.order_date)) IS NOT NULL

            UNION ALL

            SELECT strftime(
                '%Y-%m',
                date(calendar_months.month || '-01', '+1 month')
            )
            FROM calendar_months
            WHERE calendar_months.month < (
                SELECT MAX(strftime('%Y-%m', o.order_date))
                FROM orders o
                JOIN order_items i ON i.order_id = o.order_id
                WHERE o.status = 'completed'
            )
        ),
        monthly_totals AS (
            SELECT
                strftime('%Y-%m', o.order_date) AS month,
                ROUND(SUM(i.quantity * i.unit_price), 2) AS revenue
            FROM orders o
            JOIN order_items i ON i.order_id = o.order_id
            WHERE o.status = 'completed'
            GROUP BY strftime('%Y-%m', o.order_date)
        ),
        monthly_comparison AS (
            SELECT
                c.month,
                t.revenue,
                LAG(t.revenue) OVER (ORDER BY c.month)
                    AS previous_month_revenue
            FROM calendar_months c
            LEFT JOIN monthly_totals t ON t.month = c.month
        )
        SELECT
            month,
            revenue,
            previous_month_revenue,
            ROUND(revenue - previous_month_revenue, 2) AS revenue_change,
            ROUND(
                (revenue - previous_month_revenue) * 100.0
                / NULLIF(previous_month_revenue, 0),
                2
            ) AS percentage_change
        FROM monthly_comparison
        ORDER BY month
        LIMIT 100
    """,
    "highest_units_product": """
        SELECT
            p.product_name AS product_name,
            SUM(oi.quantity) AS units_sold
        FROM order_items oi
        JOIN orders o ON o.order_id = oi.order_id
        JOIN products p ON p.product_id = oi.product_id
        WHERE o.status = 'completed'
        GROUP BY p.product_id, p.product_name
        ORDER BY units_sold DESC, p.product_name ASC
        LIMIT 1
    """,
    "top_units_products": """
        SELECT
            p.product_name AS product_name,
            SUM(oi.quantity) AS units_sold
        FROM order_items oi
        JOIN orders o ON o.order_id = oi.order_id
        JOIN products p ON p.product_id = oi.product_id
        WHERE o.status = 'completed'
        GROUP BY p.product_id, p.product_name
        ORDER BY units_sold DESC, p.product_name ASC
        LIMIT 5
    """,
    "highest_profit_product": """
        SELECT
            p.product_name AS product_name,
            ROUND(
                SUM(oi.quantity * (oi.unit_price - p.unit_cost)), 2
            ) AS gross_profit
        FROM order_items oi
        JOIN orders o ON o.order_id = oi.order_id
        JOIN products p ON p.product_id = oi.product_id
        WHERE o.status = 'completed'
        GROUP BY p.product_id, p.product_name
        ORDER BY gross_profit DESC
        LIMIT 1
    """,
    "product_revenue": """
        SELECT
            p.product_name AS product_name,
            ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue
        FROM products p
        JOIN order_items oi ON oi.product_id = p.product_id
        JOIN orders o ON o.order_id = oi.order_id
        WHERE o.status = 'completed'
          AND LOWER(p.product_name) = LOWER(?)
        GROUP BY p.product_id, p.product_name
    """,
    "product_monthly_revenue": """
        WITH RECURSIVE calendar_months(month) AS (
            SELECT MIN(strftime('%Y-%m', order_date))
            FROM orders
            WHERE status = 'completed'
            HAVING MIN(strftime('%Y-%m', order_date)) IS NOT NULL

            UNION ALL

            SELECT strftime(
                '%Y-%m',
                date(month || '-01', '+1 month')
            )
            FROM calendar_months
            WHERE month < (
                SELECT MAX(strftime('%Y-%m', order_date))
                FROM orders
                WHERE status = 'completed'
            )
        ),
        monthly_totals AS (
            SELECT
                strftime('%Y-%m', o.order_date) AS month,
                ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue
            FROM orders o
            JOIN order_items oi ON oi.order_id = o.order_id
            JOIN products p ON p.product_id = oi.product_id
            WHERE o.status = 'completed'
              AND LOWER(p.product_name) = LOWER(?)
            GROUP BY strftime('%Y-%m', o.order_date)
        ),
        filled_months AS (
            SELECT
                c.month,
                COALESCE(m.revenue, 0) AS revenue
            FROM calendar_months c
            LEFT JOIN monthly_totals m ON m.month = c.month
        )
        SELECT
            month,
            revenue,
            LAG(revenue) OVER (ORDER BY month) AS previous_month_revenue,
            ROUND(
                revenue - LAG(revenue) OVER (ORDER BY month), 2
            ) AS revenue_change
        FROM filled_months
        ORDER BY month
    """,
    "product_revenue_by_date": """
        SELECT
            p.product_name AS product_name,
            COALESCE((
                SELECT ROUND(SUM(oi.quantity * oi.unit_price), 2)
                FROM order_items oi
                JOIN orders o ON o.order_id = oi.order_id
                WHERE oi.product_id = p.product_id
                  AND o.status = 'completed'
                  AND date(o.order_date) >= date(?)
                  AND date(o.order_date) <= date(?)
            ), 0) AS revenue
        FROM products p
        WHERE LOWER(p.product_name) = LOWER(?)
    """,
    "product_units": """
        SELECT
            p.product_name AS product_name,
            COALESCE(SUM(oi.quantity), 0) AS units_sold
        FROM products p
        LEFT JOIN order_items oi ON oi.product_id = p.product_id
        LEFT JOIN orders o
            ON o.order_id = oi.order_id AND o.status = 'completed'
        WHERE LOWER(p.product_name) = LOWER(?)
          AND o.order_id IS NOT NULL
        GROUP BY p.product_id, p.product_name
    """,
    "product_profit": """
        SELECT
            p.product_name AS product_name,
            ROUND(
                COALESCE(SUM(oi.quantity * (oi.unit_price - p.unit_cost)), 0),
                2
            ) AS gross_profit
        FROM products p
        JOIN order_items oi ON oi.product_id = p.product_id
        JOIN orders o ON o.order_id = oi.order_id
        WHERE o.status = 'completed'
          AND LOWER(p.product_name) = LOWER(?)
        GROUP BY p.product_id, p.product_name
    """,
    "compare_monthly_revenue": """
        WITH monthly_revenue AS (
            SELECT
                strftime('%Y-%m', o.order_date) AS month,
                ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue
            FROM orders o
            JOIN order_items oi ON oi.order_id = o.order_id
            WHERE o.status = 'completed'
              AND o.order_date >= ?
              AND o.order_date < ?
            GROUP BY strftime('%Y-%m', o.order_date)
        )
        SELECT
            ? AS first_month,
            COALESCE((
                SELECT revenue FROM monthly_revenue WHERE month = ?
            ), 0) AS first_month_revenue,
            ? AS second_month,
            COALESCE((
                SELECT revenue FROM monthly_revenue WHERE month = ?
            ), 0) AS second_month_revenue,
            ROUND(
                COALESCE((
                    SELECT revenue FROM monthly_revenue WHERE month = ?
                ), 0)
                -
                COALESCE((
                    SELECT revenue FROM monthly_revenue WHERE month = ?
                ), 0),
                2
            ) AS revenue_change,
            CASE
                WHEN COALESCE((
                    SELECT revenue FROM monthly_revenue WHERE month = ?
                ), 0) = 0 THEN NULL
                ELSE ROUND((
                    COALESCE((
                        SELECT revenue FROM monthly_revenue WHERE month = ?
                    ), 0)
                    -
                    COALESCE((
                        SELECT revenue FROM monthly_revenue WHERE month = ?
                    ), 0)
                ) * 100.0 / (
                    SELECT revenue FROM monthly_revenue WHERE month = ?
                ), 2)
            END AS percentage_change
    """,
    "revenue_by_date_range": """
        SELECT
            COALESCE(ROUND(SUM(oi.quantity * oi.unit_price), 2), 0) AS total_revenue
        FROM orders o
        JOIN order_items oi ON oi.order_id = o.order_id
        WHERE o.status = 'completed'
          AND date(o.order_date) >= date(?)
          AND date(o.order_date) <= date(?)
    """,
    "total_revenue": """
        SELECT
            ROUND(SUM(oi.quantity * oi.unit_price), 2) AS total_revenue
        FROM orders o
        JOIN order_items oi ON oi.order_id = o.order_id
        WHERE o.status = 'completed'
    """,
    "total_profit": """
        SELECT
            ROUND(
                COALESCE(
                    SUM(oi.quantity * (oi.unit_price - p.unit_cost)), 0
                ), 2
            ) AS total_profit
        FROM orders o
        JOIN order_items oi ON oi.order_id = o.order_id
        JOIN products p ON p.product_id = oi.product_id
        WHERE o.status = 'completed'
    """,
    "completed_orders": """
        SELECT COUNT(*) AS completed_orders
        FROM orders
        WHERE status = 'completed'
    """,
    "units_sold": """
        SELECT COALESCE(SUM(oi.quantity), 0) AS units_sold
        FROM orders o
        JOIN order_items oi ON oi.order_id = o.order_id
        WHERE o.status = 'completed'
    """,
    "top_products": """
        SELECT
            p.product_name AS product_name,
            ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue
        FROM order_items oi
        JOIN orders o ON o.order_id = oi.order_id
        JOIN products p ON p.product_id = oi.product_id
        WHERE o.status = 'completed'
        GROUP BY p.product_id, p.product_name
        ORDER BY revenue DESC
        LIMIT 5
    """,
    "revenue_by_category": """
        SELECT
            p.category AS category,
            ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue
        FROM order_items oi
        JOIN orders o ON o.order_id = oi.order_id
        JOIN products p ON p.product_id = oi.product_id
        WHERE o.status = 'completed'
        GROUP BY p.category
        ORDER BY revenue DESC
        LIMIT 100
    """,
    "sales_decline_by_product": """
        WITH monthly_product_revenue AS (
            SELECT
                p.product_id,
                p.product_name,
                strftime('%Y-%m', o.order_date) AS month,
                SUM(oi.quantity * oi.unit_price) AS revenue
            FROM orders o
            JOIN order_items oi ON oi.order_id = o.order_id
            JOIN products p ON p.product_id = oi.product_id
            WHERE o.status = 'completed'
              AND strftime('%Y-%m', o.order_date) IN (
                  SELECT DISTINCT strftime('%Y-%m', order_date)
                  FROM orders
                  WHERE status = 'completed'
                  ORDER BY strftime('%Y-%m', order_date) DESC
                  LIMIT 2
              )
            GROUP BY p.product_id, p.product_name, strftime('%Y-%m', o.order_date)
        ),
        compared AS (
            SELECT
                product_id,
                product_name,
                MAX(CASE WHEN month = (
                    SELECT MAX(month) FROM monthly_product_revenue
                ) THEN revenue END) AS current_revenue,
                MAX(CASE WHEN month = (
                    SELECT MIN(month) FROM monthly_product_revenue
                ) THEN revenue END) AS previous_revenue
            FROM monthly_product_revenue
            GROUP BY product_id, product_name
        )
        SELECT
            product_name,
            ROUND(COALESCE(previous_revenue, 0), 2) AS previous_revenue,
            ROUND(COALESCE(current_revenue, 0), 2) AS current_revenue,
            ROUND(COALESCE(current_revenue, 0) - COALESCE(previous_revenue, 0), 2)
                AS revenue_change
        FROM compared
        WHERE COALESCE(current_revenue, 0) < COALESCE(previous_revenue, 0)
        ORDER BY revenue_change ASC
        LIMIT 10
    """,
    "order_status_summary": """
        SELECT status, COUNT(*) AS order_count
        FROM orders
        GROUP BY status
        ORDER BY status
    """,
    "cancelled_orders": """
        SELECT COUNT(*) AS cancelled_orders
        FROM orders
        WHERE status = 'cancelled'
    """,
}



def _normalize_question(question):
    """Normalize common Hindi/Hinglish phrases into searchable keywords."""
    text = str(question).lower()

    replacements = {
        "\u0938\u092c\u0938\u0947 \u091c\u094d\u092f\u093e\u0926\u093e": " highest ",
        "\u0938\u092c\u0938\u0947 \u091c\u094d\u092f\u093e\u0926\u093e": " highest ",
        "\u0938\u092c\u0938\u0947 \u0905\u0927\u093f\u0915": " highest ",
        "\u0915\u0941\u0932 \u092c\u093f\u0915\u094d\u0930\u0940": " total sales ",
        "\u092c\u093f\u0915\u094d\u0930\u0940": " sales ",
        "\u0930\u093e\u091c\u0938\u094d\u0935": " revenue ",
        "\u092e\u0941\u0928\u093e\u092b\u093e": " profit ",
        "\u0932\u093e\u092d": " profit ",
        "\u092a\u094d\u0930\u094b\u0921\u0915\u094d\u091f": " product ",
        "\u0909\u0924\u094d\u092a\u093e\u0926": " product ",
        "\u0915\u093f\u0924\u0928\u093e": " how much ",
        "\u0915\u093f\u0924\u0928\u0940": " how much ",
        "\u0915\u093f\u0924\u0928\u0947": " how many ",
        "\u0915\u094c\u0928 \u0938\u093e": " which product ",
        "\u0915\u094c\u0928 \u0938\u0940": " which product ",
        "\u0915\u094c\u0928": " which ",
        "\u0915\u094d\u092f\u093e": " what ",
        "\u0915\u0941\u0932": " total ",
        "\u092e\u0939\u0940\u0928\u0947": " month ",
        "\u092e\u093e\u0938\u093f\u0915": " monthly ",
        "\u0936\u094d\u0930\u0947\u0923\u0940": " category ",
        "\u0936\u094d\u0930\u0947\u0923\u093f\u092f\u093e\u0901": " categories ",
        "\u092c\u093f\u0915\u0947": " sold ",
        "\u092c\u093f\u0915\u094d\u0930\u0940 \u0939\u0941\u0908": " sales ",
        "\u0930\u0926\u094d\u0926": " cancelled ",
        "\u0911\u0930\u094d\u0921\u0930": " orders ",
        "\u092a\u0942\u0930\u0947": " completed ",
        "\u0939\u0941\u090f": " ",
        "\u0914\u0930": " and ",
        "sabse zyada": " highest ",
        "sabse jyada": " highest ",
        "sabse adhik": " highest ",
        "kaun sa": " which product ",
        "kaunsa": " which product ",
        "kaunsi": " which product ",
        "kitna": " how much ",
        "kitne": " how many ",
        "kitni": " how much ",
        "kul": " total ",
        "bikri": " sales ",
        "munafa": " profit ",
        "labh": " profit ",
        "mahine": " month ",
        "mahina": " month ",
        "kitne order": " how many orders ",
    }

    for phrase, replacement in sorted(
        replacements.items(), key=lambda item: len(item[0]), reverse=True
    ):
        text = text.replace(phrase, replacement)

    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()



def _split_questions(question):
    """Split a message into separate questions without splitting every 'and'."""
    text = str(question).strip()
    if not text:
        return []

    parts = re.split(r"[?;!\n]+", text)
    questions = []

    starters = (
        r"what|which|who|how|show|compare|list|give|calculate|"
        r"tell|find|count|is|are|do|does|"
        r"kitna|kitne|kitni|kya|kaun|kis|"
        r"total|monthly|top"
    )
    for part in parts:
        part = part.strip(" .,\t")
        if not part:
            continue

        split_parts = re.split(
            rf"\s+(?:and|also|as well as|aur|or)\s+(?=(?:{starters})\b)",
            part,
            flags=re.IGNORECASE,
        )
        questions.extend(item.strip() for item in split_parts if item.strip())

    return questions


def interpret_question(question):
    """Map supported English, Hindi, and Hinglish questions to safe templates."""
    text = _normalize_question(question)

    if not text:
        raise ValueError("Please enter a business question.")

    # Ask for clarification when "best" is not defined.
    if (
        "best" in text
        and not any(
            word in text
            for word in ("revenue", "sales", "profit", "units", "unit")
        )
    ):
        raise ValueError(
            "What do you mean by 'best' product? "
            "You can compare products by revenue, profit, or units sold."
        )

    if (
        ("cancelled" in text or "canceled" in text or "cancel" in text)
        and "order" in text
    ):
        return "cancelled_orders", "Count cancelled orders"

    if (
        any(word in text for word in ("decline", "declined", "declining", "decrease", "decreased", "decreasing", "drop", "dropped", "fall", "fallen", "falling"))
        and any(word in text for word in ("revenue", "sales"))
    ):
        return "sales_decline_by_product", "Find products with declining revenue across the two latest available months"

    if (
        ("month" in text or "monthly" in text)
        and ("revenue" in text or "sales" in text)
    ):
        return "monthly_revenue", "Compare revenue month by month"

    if (
        ("category" in text or "categories" in text)
        and ("revenue" in text or "sales" in text)
    ):
        return "revenue_by_category", "Compare revenue by product category"

    if (
        ("unit" in text or "units" in text or "quantity" in text)
        and any(word in text for word in ("top 5", "top five", "top products", "all products"))
        and any(word in text for word in ("sold", "sell", "units", "quantity"))
    ):
        return "top_units_products", "Rank products by units sold"

    if (
        ("unit" in text or "units" in text)
        and any(
            word in text
            for word in ("highest", "most", "top", "which product", "best")
        )
    ):
        return "highest_units_product", "Find the product with the highest units sold"

    if (
        ("profit" in text or "profitable" in text)
        and any(word in text for word in ("highest", "most", "top", "which", "product"))
    ):
        return "highest_profit_product", "Find the product with the highest gross profit"

    if "profit" in text or "profitable" in text:
        return "total_profit", "Calculate total profit from completed orders"

    if (
        ("revenue" in text or "sales" in text)
        and any(word in text for word in ("highest", "most", "top", "best", "which product"))
    ):
        if any(word in text for word in ("top 5", "top five", "top products", "all products")):
            return "top_products", "Rank products by revenue"
        return "highest_revenue_product", "Find the product with the highest revenue"

    # Never reinterpret a product-specific revenue request as total revenue.
    product_specific = any(phrase in text for phrase in (
        "for a product", "for product", "for the product",
        "of a product", "of product", "of the product",
        "product that does not exist", "nonexistent product",
        "non-existent product", "unknown product",
    ))
    if product_specific and ("revenue" in text or "sales" in text):
        raise ValueError(
            "I could not identify a specific product for this question. "
            "Please use a product name that exists in the database. "
            "Product-specific revenue lookup is not supported yet."
        )

    if "revenue" in text or "sales" in text:
        return "total_revenue", "Calculate total revenue from completed orders"

    if "unit" in text and any(word in text for word in ("sold", "sell")):
        return "units_sold", "Calculate units sold in completed orders"

    if (
        "order" in text
        and any(word in text for word in ("status", "statuses", "breakdown", "summary"))
    ):
        return "order_status_summary", "Summarize order counts by status"

    if "order" in text and any(
        word in text for word in ("completed", "count", "how many", "total")
    ):
        return "completed_orders", "Count completed orders"

    if any(word in text for word in ("top products", "top 5", "top five")):
        return "top_products", "Rank products by revenue"

    raise ValueError(
        "I couldn't confidently interpret this question. "
        "Try asking about revenue, monthly sales, products, profit, units, "
        "categories, or orders."
    )


def resolve_follow_up_question(question, previous_question=""):
    """Resolve supported revenue/profit follow-ups from prior question context."""
    if not isinstance(question, str) or not question.strip():
        return question

    raw = question.strip().lower().strip(" \t\r\n,;.!?")
    match = re.match(
        r"^(?:(?:and|also|aur|or|what about|how about)\b)\s*",
        raw,
    )
    follow_up = raw[match.end():].strip(" \t,;:!?") if match else raw

    profit_terms = {"profit", "profits", "gross profit", "munafa"}
    revenue_terms = {"revenue", "sales", "turnover", "income", "kamai"}

    if follow_up not in profit_terms | revenue_terms:
        return question
    if not isinstance(previous_question, str) or not previous_question.strip():
        return question

    try:
        previous_intent, _ = interpret_question(previous_question)
    except (ValueError, TypeError, AttributeError):
        return question

    if follow_up in profit_terms:
        if previous_intent == "highest_revenue_product":
            return "Which product has the highest gross profit?"
        if previous_intent == "total_revenue":
            return "What is the total profit?"

    if follow_up in revenue_terms:
        if previous_intent == "highest_profit_product":
            return "Which product generated the most revenue?"
        if previous_intent == "total_profit":
            return "What is the total revenue?"

    return question


def validate_read_only_sql(query):
    """Validate one SELECT statement and allow only known database tables."""
    if not isinstance(query, str) or not query.strip():
        raise ValueError("The SQL query is empty.")

    try:
        statements = sqlglot.parse(query, read="sqlite")
    except sqlglot.errors.ParseError as exc:
        raise ValueError("The generated SQL could not be parsed safely.") from exc

    statements = [statement for statement in statements if statement is not None]

    if len(statements) != 1:
        raise ValueError("Only one SQL statement is allowed.")

    tree = statements[0]

    if not isinstance(tree, exp.Select):
        raise ValueError("Only read-only SELECT queries are allowed.")

    # Exclude CTE aliases while validating actual database tables.
    cte_names = {
        cte.alias_or_name.lower()
        for cte in tree.find_all(exp.CTE)
    }

    table_names = {
        table.name.lower()
        for table in tree.find_all(exp.Table)
        if table.name.lower() not in cte_names
    }

    if not table_names or not table_names.issubset(ALLOWED_TABLES):
        raise ValueError("The query references an unsupported database table.")

    return tree.sql(dialect="sqlite", pretty=True)

def execute_read_only_sql(query, parameters=()):
    """Run validated SQL against SQLite using a read-only connection."""
    safe_query = validate_read_only_sql(query)

    database_uri = f"{DATABASE_PATH.resolve().as_uri()}?mode=ro"

    try:
        with sqlite3.connect(
            database_uri,
            uri=True,
            timeout=5,
        ) as connection:
            connection.execute("PRAGMA query_only = ON")
            connection.set_authorizer(_read_only_authorizer)

            cursor = connection.execute(safe_query, parameters)
            rows = cursor.fetchall()
            columns = [item[0] for item in cursor.description or []]

        return columns, [tuple(row) for row in rows]

    except sqlite3.Error as exc:
        raise ValueError(
            "The read-only database query could not be completed. "
            "Please check the question and try again."
        ) from exc


def _read_only_authorizer(action, arg1, arg2, database, source):
    """SQLite-level safeguard against writes and database modifications."""
    allowed_actions = {
        sqlite3.SQLITE_SELECT,
        sqlite3.SQLITE_READ,
        sqlite3.SQLITE_FUNCTION,
        sqlite3.SQLITE_RECURSIVE,
    }

    if action in allowed_actions:
        return sqlite3.SQLITE_OK

    return sqlite3.SQLITE_DENY



def _find_product_name(question):
    """Find an exact product name mentioned in a question."""
    _, rows = execute_read_only_sql(
        "SELECT product_name FROM products"
    )
    normalized_question = _normalize_question(question)

    for row in rows:
        product_name = row[0]
        normalized_name = _normalize_question(product_name)
        if normalized_name and re.search(
            rf"\b{re.escape(normalized_name)}\b",
            normalized_question,
        ):
            return product_name

    return None


def _resolve_date_range(question):
    """Resolve common English date phrases into inclusive ISO date bounds."""
    text = _normalize_question(question)
    today = date.today()

    if "last 30 days" in text or "past 30 days" in text:
        return (today - timedelta(days=29)).isoformat(), today.isoformat()

    if "this month" in text or "current month" in text:
        start = today.replace(day=1)
        return start.isoformat(), today.isoformat()

    if "last month" in text or "previous month" in text:
        first_this_month = today.replace(day=1)
        last_previous_month = first_this_month - timedelta(days=1)
        first_previous_month = last_previous_month.replace(day=1)
        return first_previous_month.isoformat(), last_previous_month.isoformat()

    month_names = {
        name.lower(): number
        for number, name in enumerate(calendar.month_name)
        if name
    }
    for month_name, month_number in month_names.items():
        if re.search(rf"\b{month_name}\b", text):
            year_match = re.search(r"\b(20\d{2})\b", text)
            year = int(year_match.group(1)) if year_match else today.year
            start = date(year, month_number, 1)
            end = date(year, month_number, calendar.monthrange(year, month_number)[1])
            return start.isoformat(), end.isoformat()

    return None


def answer_question(question, filter_context=None):
    """Answer supported questions independently using validated read-only SQL."""
    questions = _split_questions(question)
    if not questions:
        raise ValueError("Please enter a business question.")

    answers = []
    previous_question = ""

    for item in questions:
        context_question = previous_question
        resolved_item = resolve_follow_up_question(item, context_question)
        follow_up_context = (
            context_question
            if resolved_item != item and context_question
            else None
        )

        product_name = None
        try:
            product_name = _find_product_name(resolved_item)
            normalized_question = _normalize_question(resolved_item)
            words = normalized_question.split()

            ranking_requested = any(
                word in words for word in ("highest", "most", "top", "best")
            )

            product_metric = None

            if any(word in words for word in ("profit", "profitable", "munafa")):
                product_metric = "product_profit"
            elif any(word in words for word in ("units", "unit", "quantity")):
                product_metric = "product_units"
            elif any(word in words for word in ("revenue", "sales")):
                product_metric = "product_revenue"

            product_metric_requested = (
                product_name is not None
                and product_metric is not None
                and not ranking_requested
                and "which product" not in normalized_question
            )

            if product_metric_requested:
                intent = product_metric
                metric_labels = {
                    "product_revenue": "revenue",
                    "product_profit": "gross profit",
                    "product_units": "units sold",
                }
                interpretation = (
                    f"Calculate {metric_labels[intent]} for {product_name}"
                )
            else:
                product_name = None
                intent, interpretation = interpret_question(resolved_item)

            comparison_text = _normalize_question(resolved_item)
            comparison_words = comparison_text.split()
            month_numbers = {
                "january": "01", "february": "02", "march": "03",
                "april": "04", "may": "05", "june": "06",
                "july": "07", "august": "08", "september": "09",
                "october": "10", "november": "11", "december": "12",
            }
            comparison_months = [
                (name, number) for name, number in month_numbers.items()
                if name in comparison_words
            ]
            comparison_year = re.search(r"\b(20\d{2})\b", comparison_text)
            comparison_requested = (
                any(word in comparison_words for word in ("compare", "comparison", "versus", "vs"))
                and len(comparison_months) >= 2
                and comparison_year is not None
                and any(word in comparison_words for word in ("revenue", "sales"))
            )
            if comparison_requested:
                first_month = f"{comparison_year.group(1)}-{comparison_months[0][1]}"
                second_month = f"{comparison_year.group(1)}-{comparison_months[1][1]}"
                intent = "compare_monthly_revenue"
                interpretation = f"Compare completed-order revenue for {first_month} and {second_month}"

            date_range = _resolve_date_range(resolved_item)
            asks_for_revenue = any(
                word in words for word in ("revenue", "sales")
            )
            asks_for_monthly_trend = (
                product_name is not None
                and asks_for_revenue
                and any(word in words for word in ("monthly", "month"))
                and not date_range
                and not ranking_requested
            )

            if comparison_requested:
                pass
            elif asks_for_monthly_trend:
                intent = "product_monthly_revenue"
                interpretation = (
                    f"Show monthly revenue trend for {product_name}"
                )
            elif (
                date_range is not None
                and asks_for_revenue
                and product_name is not None
                and not ranking_requested
            ):
                intent = "product_revenue_by_date"
                interpretation = (
                    f"Calculate revenue for {product_name} from "
                    f"{date_range[0]} through {date_range[1]}"
                )
            elif (
                date_range is not None
                and asks_for_revenue
                and product_name is None
                and not ranking_requested
            ):
                intent = "revenue_by_date_range"
                interpretation = (
                    f"Calculate completed-order revenue from "
                    f"{date_range[0]} through {date_range[1]}"
                )
            if comparison_requested:
                intent = "compare_monthly_revenue"
                interpretation = (
                    f"Compare completed-order revenue for "
                    f"{first_month} and {second_month}"
                )

        except ValueError as exc:
            from core.ai_sql_generator import generate_sql

            ai_answered = False
            previous_attempt_sql = None
            generation_error = None

            for attempt in range(3):
                generated_sql = None
                try:
                    if attempt == 0:
                        generated_sql = generate_sql(resolved_item)
                    else:
                        generated_sql = generate_sql(
                            resolved_item,
                            previous_sql=previous_attempt_sql,
                            error_message=str(generation_error),
                        )

                    if not generated_sql:
                        break

                    safe_sql = validate_read_only_sql(generated_sql)
                    columns, rows = execute_read_only_sql(safe_sql)

                    previous_question = resolved_item
                    answers.append({
                        "question": item,
                        "resolved_question": resolved_item,
                        "intent": "ai_generated_select",
                        "follow_up_context": follow_up_context,
                        "interpretation": "AI-generated read-only SQL",
                        "error": None,
                        "sql": safe_sql,
                        "validation_status": "Passed",
                        "execution_status": "Succeeded",
                        "columns": columns,
                        "rows": rows,
                        "row_count": len(rows),
                        "retry_count": attempt,
                    })
                    ai_answered = True
                    break

                except (
                    ValueError,
                    RuntimeError,
                    OSError,
                    KeyError,
                    IndexError,
                    TypeError,
                ) as retry_error:
                    if isinstance(generated_sql, str) and generated_sql.strip():
                        previous_attempt_sql = generated_sql
                    generation_error = retry_error

            if ai_answered:
                continue

            fallback_error = None
            if generation_error is not None:
                fallback_error = (
                    f"AI SQL fallback failed after {attempt + 1} attempt(s): "
                    f"{generation_error}"
                )

            answers.append({
                "question": item,
                "resolved_question": resolved_item,
                "intent": None,
                "follow_up_context": follow_up_context,
                "interpretation": "Question not supported",
                "error": fallback_error or str(exc),
                "sql": None,
                "validation_status": "Not run",
                "execution_status": "Not run",
                "columns": [],
                "rows": [],
                "row_count": 0,
            })
            continue

        ranking_intents = {
            "highest_revenue_product",
            "top_products",
            "highest_units_product",
            "top_units_products",
            "highest_profit_product",
        }
        ranking_parameters = []
        sql_query = QUERY_TEMPLATES[intent]

        # Preserve Top 5 requests when clarification changes the resolved question.
        top5_context = " ".join(
            value
            for value in (resolved_item, filter_context)
            if isinstance(value, str)
        )
        if (
            intent == "highest_profit_product"
            and re.search(r"\btop\s+(?:5|five)\b", top5_context, re.IGNORECASE)
        ):
            sql_query = re.sub(
                r"\bLIMIT\s+1\b",
                "LIMIT 5",
                sql_query,
                count=1,
                flags=re.IGNORECASE,
            )
        if intent in ranking_intents:
            filter_question = (
                filter_context
                if isinstance(filter_context, str) and filter_context.strip()
                else resolved_item
            )
            category_names = (
                "Home Office",
                "Electronics",
                "Accessories",
                "Stationery",
                "Lifestyle",
            )
            matched_category = next(
                (
                    category
                    for category in category_names
                    if re.search(
                        rf"\b{re.escape(category)}\b",
                        filter_question,
                        flags=re.IGNORECASE,
                    )
                ),
                None,
            )
            ranking_date_range = _resolve_date_range(filter_question)
            filter_clauses = []

            if matched_category:
                filter_clauses.append("p.category = ?")
                ranking_parameters.append(matched_category)

            if ranking_date_range:
                filter_clauses.extend(
                    [
                        "date(o.order_date) >= date(?)",
                        "date(o.order_date) <= date(?)",
                    ]
                )
                ranking_parameters.extend(ranking_date_range)

            if filter_clauses:
                where_marker = "WHERE o.status = 'completed'"
                if where_marker not in sql_query:
                    raise ValueError(
                        "The ranking query cannot safely apply the requested filters."
                    )
                sql_query = sql_query.replace(
                    where_marker,
                    where_marker + " AND " + " AND ".join(filter_clauses),
                    1,
                )

        safe_sql = validate_read_only_sql(sql_query)
        if intent == "compare_monthly_revenue":
            earliest = min(first_month, second_month)
            latest = max(first_month, second_month)

            next_month_date = date.fromisoformat(latest + "-01")
            if next_month_date.month == 12:
                next_month_date = date(next_month_date.year + 1, 1, 1)
            else:
                next_month_date = date(
                    next_month_date.year,
                    next_month_date.month + 1,
                    1,
                )

            parameters = (
                earliest + "-01",
                next_month_date.isoformat(),
                first_month, first_month,
                second_month, second_month,
                second_month, first_month,
                first_month, second_month,
                first_month, first_month,
            )
        elif intent == "revenue_by_date_range":
            parameters = date_range
        elif intent == "product_revenue_by_date":
            parameters = (*date_range, product_name)
        elif intent in (
            "product_monthly_revenue",
            "product_revenue",
            "product_profit",
            "product_units",
        ):
            parameters = (product_name,)
        elif intent in ranking_intents:
            parameters = tuple(ranking_parameters)
        else:
            parameters = ()
        columns, rows = execute_read_only_sql(safe_sql, parameters)
        previous_question = resolved_item
        answers.append({
            "question": item,
            "resolved_question": resolved_item,
            "intent": intent,
            "follow_up_context": follow_up_context,
            "interpretation": interpretation,
            "error": None,
            "sql": safe_sql,
            "validation_status": "Passed",
            "execution_status": "Succeeded",
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
        })

    if len(answers) == 1:
        if answers[0].get("error"):
            raise ValueError(answers[0]["error"])
        return answers[0]

    successful = [a for a in answers if not a.get("error")]

    if not successful:
        return {
            "interpretation": "No questions could be answered.",
            "sql": "",
            "columns": [],
            "rows": [],
            "row_count": 0,
            "answers": answers,
            "error": "None of the questions could be interpreted.",
        }

    combined_columns = ["question"]
    for answer in successful:
        for column in answer["columns"]:
            if column not in combined_columns:
                combined_columns.append(column)

    combined_rows = []
    for answer in successful:
        for row in answer["rows"]:
            row_map = dict(zip(answer["columns"], row))
            combined_rows.append(tuple(
                answer["question"] if col == "question"
                else row_map.get(col)
                for col in combined_columns
            ))

    combined_sql = "\n\n".join(
        f"-- Question {i}: {a['question']}\n{a['sql']}"
        for i, a in enumerate(successful, start=1)
    )

    return {
        "interpretation": " | ".join(
            f"{i}. {a['interpretation']}"
            for i, a in enumerate(successful, start=1)
        ),
        "sql": combined_sql,
        "columns": combined_columns,
        "rows": combined_rows,
        "row_count": len(combined_rows),
        "answers": answers,
    }

