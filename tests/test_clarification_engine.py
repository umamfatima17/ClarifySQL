import unittest

from core.clarification_engine import detect_clarification


class TestStructuredClarification(unittest.TestCase):
    def test_ambiguous_best_product_requests_metric(self):
        result = detect_clarification("Which product is best?")
        self.assertIsNotNone(result)
        self.assertEqual(result["dimension"], "metric")
        self.assertEqual(
            result["options"],
            ["Revenue", "Gross profit", "Units sold"],
        )

    def test_hinglish_ambiguous_best_product_requests_metric(self):
        result = detect_clarification("Sabse achha product kaunsa hai?")
        self.assertIsNotNone(result)
        self.assertEqual(result["dimension"], "metric")
        self.assertEqual(
            result["options"],
            ["Revenue", "Gross profit", "Units sold"],
        )

    def test_best_product_with_explicit_metric_needs_no_metric_clarification(self):
        result = detect_clarification(
            "Which product generated the most revenue?"
        )
        self.assertIsNone(result)

    def test_top_selling_without_metric_requests_clarification(self):
        result = detect_clarification("Show top-selling products")
        self.assertIsNotNone(result)
        self.assertEqual(result["dimension"], "metric")
        self.assertEqual(result["options"], ["Revenue", "Units sold"])

    def test_revenue_choice_can_request_result_scope(self):
        result = detect_clarification(
            "Which product is best?",
            answers=["Revenue"],
        )
        self.assertIsNotNone(result)
        self.assertEqual(result["dimension"], "result_scope")
        self.assertEqual(result["step"], 2)

    def test_gross_profit_choice_requests_result_scope(self):
        result = detect_clarification(
            "Which product is best?",
            answers=["Gross profit"],
        )
        self.assertEqual(result["dimension"], "result_scope")

    def test_empty_question_does_not_request_clarification(self):
        self.assertIsNone(detect_clarification("   "))

    def test_detector_does_not_execute_or_generate_sql(self):
        result = detect_clarification("Which product is best?")
        self.assertNotIn("sql", result)


    def test_top_selling_revenue_selection_requests_scope(self):
        result = detect_clarification(
            "Show top-selling products",
            answers=["Revenue"],
        )
        self.assertIsNotNone(result)
        self.assertEqual(result["dimension"], "result_scope")
        self.assertEqual(
            result["options"],
            ["Top product only", "Top 5 products"],
        )

    def test_top_selling_units_selection_requests_result_scope(self):
        result = detect_clarification(
            "Show top-selling products",
            answers=["Units sold"],
        )
        self.assertEqual(result["dimension"], "result_scope")

    def test_best_product_units_selection_requests_result_scope(self):
        result = detect_clarification(
            "Which product is best?",
            answers=["Units sold"],
        )
        self.assertEqual(result["dimension"], "result_scope")


    def test_best_selling_items_uses_sales_metric_options(self):
        result = detect_clarification("Show best-selling items")
        self.assertIsNotNone(result)
        self.assertEqual(result["dimension"], "metric")
        self.assertEqual(result["options"], ["Revenue", "Units sold"])
    def test_popular_product_requests_metric_clarification(self):
        result = detect_clarification("Which product is most popular?")
        self.assertIsNotNone(result)
        self.assertEqual(result["dimension"], "metric")

    def test_best_selling_items_requests_metric_clarification(self):
        result = detect_clarification("Show best-selling items")
        self.assertIsNotNone(result)
        self.assertEqual(result["dimension"], "metric")

    def test_explicit_units_metric_does_not_request_metric_clarification(self):
        result = detect_clarification("Which product sold the most units?")
        self.assertIsNone(result)

    def test_unknown_answer_does_not_advance_clarification(self):
        result = detect_clarification(
            "Which product is best?",
            answers=["Something else"],
        )
        self.assertIsNone(result)

if __name__ == "__main__":
    unittest.main()

def test_scope_for_gross_profit_metric():
    from core.clarification_engine import detect_clarification

    result = detect_clarification(
        "Find the best products in Electronics",
        answers=["Gross profit"],
    )

    assert result is not None
    assert result["dimension"] == "result_scope"
    assert result["step"] == 2
    assert result["options"] == ["Top product only", "Top 5 products"]


def test_scope_for_units_sold_metric():
    from core.clarification_engine import detect_clarification

    result = detect_clarification(
        "Show top-selling products",
        answers=["Units sold"],
    )

    assert result is not None
    assert result["dimension"] == "result_scope"
    assert result["step"] == 2
    assert result["options"] == ["Top product only", "Top 5 products"]

