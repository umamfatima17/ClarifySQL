import unittest

from core.schema_inspector import get_database_schema


class TestDatabaseSchemaInspector(unittest.TestCase):

    def test_expected_tables_are_discovered(self):
        schema = get_database_schema()

        self.assertTrue(
            {"products", "orders", "order_items"}.issubset(schema)
        )

    def test_product_columns_are_discovered(self):
        schema = get_database_schema()

        self.assertIn(
            "product_name",
            [column["name"] for column in schema["products"]]
        )
        self.assertIn(
            "selling_price",
            [column["name"] for column in schema["products"]]
        )

    def test_order_columns_are_discovered(self):
        schema = get_database_schema()

        self.assertIn(
            "order_date",
            [column["name"] for column in schema["orders"]]
        )
        self.assertIn(
            "status",
            [column["name"] for column in schema["orders"]]
        )

    def test_column_metadata_has_expected_fields(self):
        schema = get_database_schema()
        product_id = next(
            column for column in schema["products"]
            if column["name"] == "product_id"
        )

        self.assertEqual(product_id["type"], "INTEGER")
        self.assertTrue(product_id["primary_key"])
        self.assertIn("not_null", product_id)


if __name__ == "__main__":
    unittest.main()
