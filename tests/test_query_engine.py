import unittest

from core.query_engine import (
    _normalize_question,
    interpret_question,
    answer_question,
    validate_read_only_sql,
    execute_read_only_sql,
    resolve_follow_up_question,
)


class TestQuestionInterpretation(unittest.TestCase):

    def test_english_total_profit(self):
        intent, _ = interpret_question("What is the total profit?")
        self.assertEqual(intent, "total_profit")

    def test_hinglish_total_profit(self):
        intent, _ = interpret_question("Total profit kitna hai?")
        self.assertEqual(intent, "total_profit")

    def test_hindi_total_profit(self):
        question = "\u0915\u0941\u0932 \u092e\u0941\u0928\u093e\u092b\u093e \u0915\u093f\u0924\u0928\u093e \u0939\u0948?"
        intent, _ = interpret_question(question)
        self.assertEqual(intent, "total_profit")

    def test_hindi_cancelled_orders(self):
        question = "\u0915\u093f\u0924\u0928\u0947 \u0911\u0930\u094d\u0921\u0930 \u0930\u0926\u094d\u0926 \u0939\u0941\u090f?"
        intent, _ = interpret_question(question)
        self.assertEqual(intent, "cancelled_orders")

    def test_declining_revenue_question_is_interpreted_correctly(self):
        intent, _ = interpret_question("Which products had declining revenue?")
        self.assertEqual(intent, "sales_decline_by_product")

    def test_order_status_summary_is_interpreted_correctly(self):
        intent, _ = interpret_question("Show order status summary")
        self.assertEqual(intent, "order_status_summary")

    def test_unknown_product_revenue_is_not_total_revenue(self):
        with self.assertRaisesRegex(ValueError, "specific product"):
            answer_question("Show revenue for a product that does not exist")

    def test_unsupported_question_is_rejected(self):
        with self.assertRaises(ValueError):
            interpret_question("Tell me a joke")


    def test_top_five_products_by_units_uses_dedicated_intent(self):
        intent, _ = interpret_question("Show the top 5 products by units sold")
        self.assertEqual(intent, "top_units_products")

    def test_top_five_products_by_units_returns_units_column(self):
        result = answer_question("Show the top 5 products by units sold")
        self.assertIsNone(result["error"])
        self.assertEqual(result["intent"], "top_units_products")
        self.assertEqual(result["validation_status"], "Passed")
        self.assertEqual(result["execution_status"], "Succeeded")
        self.assertEqual(result["row_count"], 5)
        self.assertIn("product_name", result["columns"])
        self.assertIn("units_sold", result["columns"])
        self.assertNotIn("revenue", result["columns"])


class TestFollowUpResolution(unittest.TestCase):
    def test_product_revenue_followed_by_profit(self):
        self.assertEqual(
            resolve_follow_up_question(
                "And profit?",
                "Which product generated the most revenue?",
            ),
            "Which product has the highest gross profit?",
        )

    def test_total_revenue_followed_by_hinglish_profit(self):
        self.assertEqual(
            resolve_follow_up_question(
                "Aur profit?", "What is the total revenue?"
            ),
            "What is the total profit?",
        )

    def test_total_profit_followed_by_revenue(self):
        self.assertEqual(
            resolve_follow_up_question(
                "What about revenue?", "What is the total profit?"
            ),
            "What is the total revenue?",
        )

    def test_independent_question_is_unchanged(self):
        question = "How many orders were cancelled?"
        self.assertEqual(
            resolve_follow_up_question(
                question, "What is the total revenue?"
            ),
            question,
        )

    def test_unsupported_follow_up_is_not_guessed(self):
        question = "And profit?"
        self.assertEqual(
            resolve_follow_up_question(
                question, "Compare monthly revenue."
            ),
            question,
        )


class TestMultiQuestionFollowUps(unittest.TestCase):
    def test_product_revenue_and_profit_uses_same_product_context(self):
        result = answer_question(
            "Which product generated the most revenue? And profit?"
        )
        self.assertEqual(len(result["answers"]), 2)
        profit_answer = result["answers"][1]
        self.assertIsNone(profit_answer["error"])
        self.assertEqual(profit_answer["columns"], ["product_name", "gross_profit"])
        self.assertEqual(
            profit_answer["rows"],
            [("Mechanical Keyboard", 22969.9)],
        )

    def test_follow_up_includes_explainability_metadata(self):
        result = answer_question(
            "Which product generated the most revenue? And profit?"
        )

        self.assertEqual(len(result["answers"]), 2)
        profit_answer = result["answers"][1]

        self.assertEqual(
            profit_answer["resolved_question"],
            "Which product has the highest gross profit?",
        )
        self.assertEqual(profit_answer["intent"], "highest_profit_product")
        self.assertEqual(
            profit_answer["follow_up_context"],
            "Which product generated the most revenue",
        )
        self.assertEqual(profit_answer["validation_status"], "Passed")
        self.assertEqual(profit_answer["execution_status"], "Succeeded")
        self.assertTrue(profit_answer["sql"])
        self.assertIn("SELECT", profit_answer["sql"].upper())

    def test_total_revenue_and_profit_keeps_total_context(self):
        result = answer_question("What is the total revenue? And profit?")
        self.assertEqual(len(result["answers"]), 2)
        profit_answer = result["answers"][1]
        self.assertIsNone(profit_answer["error"])
        self.assertEqual(profit_answer["columns"], ["total_profit"])
        self.assertEqual(profit_answer["rows"], [(86591.3,)])


class TestQueryResults(unittest.TestCase):

    def test_single_question_includes_explainability_metadata(self):
        result = answer_question("What is the total revenue?")

        self.assertIsNone(result["error"])
        self.assertEqual(result["resolved_question"], "What is the total revenue")
        self.assertEqual(result["intent"], "total_revenue")
        self.assertIsNone(result["follow_up_context"])
        self.assertEqual(result["validation_status"], "Passed")
        self.assertEqual(result["execution_status"], "Succeeded")
        self.assertTrue(result["sql"])
        self.assertIn("SELECT", result["sql"].upper())

    def test_total_profit_returns_numeric_result(self):
        result = answer_question("What is the total profit?")
        self.assertIsNone(result["error"])
        self.assertIn("total_profit", result["columns"])
        self.assertGreater(float(result["rows"][0][0]), 0)

    def test_hinglish_profit_returns_same_result(self):
        english = answer_question("What is the total profit?")
        hinglish = answer_question("Total profit kitna hai?")
        self.assertAlmostEqual(
            float(english["rows"][0][0]),
            float(hinglish["rows"][0][0]),
            places=2,
        )

    def test_hindi_cancelled_orders_returns_count(self):
        question = "\u0915\u093f\u0924\u0928\u0947 \u0911\u0930\u094d\u0921\u0930 \u0930\u0926\u094d\u0926 \u0939\u0941\u090f?"
        result = answer_question(question)
        self.assertIsNone(result["error"])
        self.assertEqual(result["columns"], ["cancelled_orders"])
        self.assertEqual(int(result["rows"][0][0]), 2)

    def test_declining_revenue_returns_only_declining_products(self):
        result = answer_question("Which products had declining revenue?")
        self.assertIsNone(result["error"])
        self.assertIn("product_name", result["columns"])
        self.assertGreater(len(result["rows"]), 0)
        self.assertIn("Laptop Stand", [row[0] for row in result["rows"]])
        self.assertIn("revenue_change", result["columns"])
        change_index = result["columns"].index("revenue_change")
        for row in result["rows"]:
            self.assertLess(float(row[change_index]), 0)

    def test_order_status_summary_matches_database_counts(self):
        import sqlite3
        from core.database import DATABASE_PATH

        with sqlite3.connect(DATABASE_PATH) as connection:
            expected = connection.execute(
                "SELECT status, COUNT(*) FROM orders GROUP BY status ORDER BY status"
            ).fetchall()

        result = answer_question("Show order status summary")
        self.assertIsNone(result["error"])
        self.assertEqual(result["columns"], ["status", "order_count"])
        self.assertEqual(result["rows"], expected)

    def test_total_revenue_returns_numeric_result(self):
        result = answer_question("What is the total revenue?")
        self.assertIsNone(result["error"])
        self.assertGreater(float(result["rows"][0][0]), 0)


class TestSQLSafety(unittest.TestCase):

    def test_select_from_allowed_table(self):
        sql = validate_read_only_sql(
            "SELECT product_id FROM products"
        )
        self.assertIn("SELECT", sql.upper())

    def test_delete_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_read_only_sql("DELETE FROM orders")

    def test_unknown_table_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_read_only_sql(
                "SELECT * FROM secret_table"
            )

    def test_multiple_statements_are_rejected(self):
        with self.assertRaises(ValueError):
            validate_read_only_sql(
                "SELECT 1; SELECT 2"
            )

    def test_database_execution_rejects_delete(self):
        with self.assertRaises(ValueError):
            execute_read_only_sql("DELETE FROM orders")


class TestAdditionalReliability(unittest.TestCase):

    def test_ambiguous_best_question_requests_clarification(self):
        with self.assertRaisesRegex(ValueError, "What do you mean"):
            answer_question("Which product is best?")

    def test_highest_units_product_returns_product_and_unit_count(self):
        result = answer_question("Which product sold the most units?")

        self.assertIsNone(result["error"])
        self.assertEqual(result["intent"], "highest_units_product")
        self.assertEqual(result["columns"], ["product_name", "units_sold"])
        self.assertEqual(len(result["rows"]), 1)
        self.assertGreater(int(result["rows"][0][1]), 0)
        self.assertEqual(result["validation_status"], "Passed")
        self.assertEqual(result["execution_status"], "Succeeded")

    def test_no_matching_records_returns_empty_rows(self):
        columns, rows = execute_read_only_sql(
            "SELECT product_id FROM products "
            "WHERE product_name = 'ClarifySQL_Test_No_Such_Product'"
        )
        self.assertEqual(columns, ["product_id"])
        self.assertEqual(rows, [])

    def test_invalid_sql_is_rejected(self):
        with self.assertRaises(ValueError):
            execute_read_only_sql("SELEC FROM")

    def test_drop_table_is_rejected(self):
        with self.assertRaises(ValueError):
            execute_read_only_sql("DROP TABLE products")

    def test_insert_is_rejected(self):
        with self.assertRaises(ValueError):
            execute_read_only_sql(
                "INSERT INTO products (product_id) VALUES (999999)"
            )

    def test_top_five_products_match_independent_calculation(self):
        import sqlite3
        from core.database import DATABASE_PATH

        with sqlite3.connect(DATABASE_PATH) as connection:
            expected = connection.execute("""
                SELECT p.product_name,
                       ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue
                FROM orders o
                JOIN order_items oi ON oi.order_id = o.order_id
                JOIN products p ON p.product_id = oi.product_id
                WHERE o.status = 'completed'
                GROUP BY p.product_id, p.product_name
                ORDER BY revenue DESC, p.product_name
                LIMIT 5
            """).fetchall()

        result = answer_question("Show top 5 products by revenue")
        actual = [
            (row[0], round(float(row[1]), 2))
            for row in result["rows"]
        ]
        self.assertEqual(actual, [(row[0], round(row[1], 2)) for row in expected])

    def test_monthly_revenue_marks_missing_month_comparison_unavailable(self):
        import sqlite3
        from core.query_engine import QUERY_TEMPLATES

        connection = sqlite3.connect(":memory:")
        self.addCleanup(connection.close)

        connection.executescript("""
            CREATE TABLE orders (
                order_id INTEGER PRIMARY KEY,
                order_date TEXT NOT NULL,
                status TEXT NOT NULL
            );
            CREATE TABLE order_items (
                order_item_id INTEGER PRIMARY KEY,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL
            );

            INSERT INTO orders VALUES
                (1, '2026-01-31', 'completed'),
                (2, '2026-03-01', 'completed'),
                (3, '2026-03-31', 'completed');

            INSERT INTO order_items VALUES
                (1, 1, 1, 2, 10.00),
                (2, 2, 1, 1, 30.00),
                (3, 3, 1, 1, 20.00);
        """)

        rows = connection.execute(
            QUERY_TEMPLATES["monthly_revenue"]
        ).fetchall()

        self.assertEqual(
            [row[0] for row in rows],
            ["2026-01", "2026-02", "2026-03"],
        )
        self.assertEqual([row[1] for row in rows], [20.0, None, 50.0])
        self.assertEqual([row[2] for row in rows], [None, 20.0, None])
        self.assertIsNone(rows[2][3])
        self.assertIsNone(rows[2][4])


    def test_month_end_dates_and_missing_calendar_month(self):
        import sqlite3

        connection = sqlite3.connect(":memory:")
        self.addCleanup(connection.close)

        connection.executescript("""
            CREATE TABLE orders (
                order_id INTEGER PRIMARY KEY,
                order_date TEXT NOT NULL,
                status TEXT NOT NULL
            );
            CREATE TABLE order_items (
                order_item_id INTEGER PRIMARY KEY,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL
            );
            INSERT INTO orders VALUES
                (1, '2026-01-31', 'completed'),
                (2, '2026-03-01', 'completed'),
                (3, '2026-03-31', 'completed'),
                (4, '2026-02-28', 'cancelled');
            INSERT INTO order_items VALUES
                (1, 1, 1, 2, 10.00),
                (2, 2, 1, 1, 30.00),
                (3, 3, 1, 1, 20.00),
                (4, 4, 1, 100, 99.00);
        """)

        rows = connection.execute("""
            SELECT
                strftime('%Y-%m', o.order_date) AS month,
                ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue
            FROM orders o
            JOIN order_items oi ON oi.order_id = o.order_id
            WHERE o.status = 'completed'
              AND date(o.order_date) IS NOT NULL
            GROUP BY strftime('%Y-%m', o.order_date)
            ORDER BY month
        """).fetchall()

        self.assertEqual(rows, [
            ("2026-01", 20.0),
            ("2026-03", 50.0),
        ])

        # The cancelled February order must not affect revenue.
        self.assertNotIn(("2026-02", 9900.0), rows)

        # March 1 and March 31 must both belong to March.
        march = next(row for row in rows if row[0] == "2026-03")
        self.assertEqual(march[1], 50.0)

    def test_monthly_revenue_matches_independent_calculation(self):
        import sqlite3
        from core.database import DATABASE_PATH

        with sqlite3.connect(DATABASE_PATH) as connection:
            expected = connection.execute("""
                SELECT strftime('%Y-%m', o.order_date) AS month,
                       ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue
                FROM orders o
                JOIN order_items oi ON oi.order_id = o.order_id
                WHERE o.status = 'completed'
                GROUP BY strftime('%Y-%m', o.order_date)
                ORDER BY month
            """).fetchall()

        result = answer_question("Show monthly revenue")
        actual = [
            (row[0], round(float(row[1]), 2))
            for row in result["rows"]
        ]
        self.assertEqual(
            actual,
            [(row[0], round(row[1], 2)) for row in expected],
        )

        months = [row[0] for row in result["rows"]]
        self.assertEqual(months, sorted(months))

        for index in range(1, len(result["rows"])):
            self.assertAlmostEqual(
                float(result["rows"][index][2]),
                float(result["rows"][index - 1][1]),
                places=2,
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
