
import random
import sqlite3
from contextlib import closing
from calendar import monthrange
from datetime import date
from pathlib import Path


# Keep the database inside the project's data folder.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "data" / "clarifysql.db"


PRODUCTS = [
    (1, "Wireless Mouse", "Electronics", 350.00, 599.00),
    (2, "Mechanical Keyboard", "Electronics", 1200.00, 1999.00),
    (3, "Laptop Stand", "Accessories", 450.00, 799.00),
    (4, "USB-C Hub", "Electronics", 700.00, 1199.00),
    (5, "Desk Lamp", "Home Office", 500.00, 899.00),
    (6, "Notebook Set", "Stationery", 120.00, 249.00),
    (7, "Water Bottle", "Lifestyle", 180.00, 349.00),
    (8, "Backpack", "Lifestyle", 650.00, 1099.00),
]

# Order counts decrease in the later months to create
# varied business activity for analysis and demonstrations.
MONTHLY_ORDER_COUNTS = {
    1: 10,
    2: 11,
    3: 12,
    4: 10,
    5: 8,
    6: 7,
}


def get_connection():
    """Open a connection to the project's SQLite database."""
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def create_tables(connection):
    """Create the database tables if they do not exist."""
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER PRIMARY KEY,
            product_name TEXT NOT NULL,
            category TEXT NOT NULL,
            unit_cost REAL NOT NULL CHECK (unit_cost >= 0),
            selling_price REAL NOT NULL CHECK (selling_price >= 0)
        );

        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY,
            order_date TEXT NOT NULL,
            customer_id INTEGER NOT NULL,
            status TEXT NOT NULL
                CHECK (status IN ('completed', 'cancelled'))
        );

        CREATE TABLE IF NOT EXISTS order_items (
            order_item_id INTEGER PRIMARY KEY,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL CHECK (quantity > 0),
            unit_price REAL NOT NULL CHECK (unit_price >= 0),

            FOREIGN KEY (order_id)
                REFERENCES orders(order_id),

            FOREIGN KEY (product_id)
                REFERENCES products(product_id)
        );

        CREATE INDEX IF NOT EXISTS idx_orders_date
            ON orders(order_date);

        CREATE INDEX IF NOT EXISTS idx_order_items_order
            ON order_items(order_id);
        """
    )


def seed_products(connection):
    """Insert the sample product catalogue once."""
    connection.executemany(
        """
        INSERT OR IGNORE INTO products
        (product_id, product_name, category, unit_cost, selling_price)
        VALUES (?, ?, ?, ?, ?)
        """,
        PRODUCTS,
    )


def seed_sales(connection):
    """Generate reproducible sample orders from January to June 2026."""
    existing_orders = connection.execute(
        "SELECT COUNT(*) FROM orders"
    ).fetchone()[0]

    if existing_orders > 0:
        return

    rng = random.Random(42)
    order_id = 1
    item_id = 1

    for month, order_count in MONTHLY_ORDER_COUNTS.items():
        days_in_month = monthrange(2026, month)[1]

        for order_number in range(order_count):
            day = rng.randint(1, days_in_month)
            order_date = date(2026, month, day).isoformat()

            # A small number of orders are cancelled.
            status = (
                "cancelled"
                if order_number == order_count - 1 and month in (2, 5)
                else "completed"
            )

            customer_id = rng.randint(1001, 1025)

            connection.execute(
                """
                INSERT INTO orders
                (order_id, order_date, customer_id, status)
                VALUES (?, ?, ?, ?)
                """,
                (order_id, order_date, customer_id, status),
            )

            # Each order contains one to three distinct products.
            item_count = rng.randint(1, 3)
            selected_products = rng.sample(PRODUCTS, item_count)

            for product in selected_products:
                product_id = product[0]
                list_price = product[4]

                # Keep historical order prices independent
                # from future catalogue price changes.
                discount = rng.choice([0.0, 0.0, 0.05, 0.10])
                unit_price = round(list_price * (1 - discount), 2)
                quantity = rng.randint(1, 4)

                connection.execute(
                    """
                    INSERT INTO order_items
                    (order_item_id, order_id, product_id, quantity, unit_price)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        item_id,
                        order_id,
                        product_id,
                        quantity,
                        unit_price,
                    ),
                )

                item_id += 1

            order_id += 1


def initialize_database():
    """Create tables and populate an empty sample database."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    with closing(get_connection()) as connection:
        with connection:
            # Enforce foreign-key relationships for this connection.
            connection.execute("PRAGMA foreign_keys = ON")

            create_tables(connection)
            seed_products(connection)
            seed_sales(connection)


def get_database_summary():
    """Return basic counts to verify the database."""
    with closing(get_connection()) as connection:
        with connection:
            product_count = connection.execute(
                "SELECT COUNT(*) FROM products"
            ).fetchone()[0]

            order_count = connection.execute(
                "SELECT COUNT(*) FROM orders"
            ).fetchone()[0]

            item_count = connection.execute(
                "SELECT COUNT(*) FROM order_items"
            ).fetchone()[0]

            completed_orders = connection.execute(
                """
                SELECT COUNT(*)
                FROM orders
                WHERE status = 'completed'
                """
            ).fetchone()[0]

        return {
            "products": product_count,
            "orders": order_count,
            "order_items": item_count,
            "completed_orders": completed_orders,
            "database_path": str(DATABASE_PATH),
        }


if __name__ == "__main__":
    initialize_database()
    summary = get_database_summary()

    print("ClarifySQL database initialized successfully.")
    for key, value in summary.items():
        print(f"{key}: {value}")
