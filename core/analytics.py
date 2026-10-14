
from contextlib import closing

from core.database import get_connection


def get_overall_metrics():
    """Calculate business metrics from completed orders only."""

    query = """
        SELECT
            COUNT(DISTINCT o.order_id) AS total_orders,
            COALESCE(SUM(oi.quantity), 0) AS units_sold,
            COALESCE(SUM(oi.quantity * oi.unit_price), 0)
                AS total_revenue,
            COALESCE(SUM(oi.quantity * p.unit_cost), 0)
                AS total_cost
        FROM orders AS o
        JOIN order_items AS oi
            ON o.order_id = oi.order_id
        JOIN products AS p
            ON oi.product_id = p.product_id
        WHERE o.status = 'completed'
    """

    with closing(get_connection()) as connection:
        result = connection.execute(query).fetchone()

    revenue = result["total_revenue"]
    cost = result["total_cost"]

    return {
        "total_orders": result["total_orders"],
        "units_sold": result["units_sold"],
        "total_revenue": round(revenue, 2),
        "total_cost": round(cost, 2),
        "total_profit": round(revenue - cost, 2),
    }


def get_monthly_performance():
    """Calculate monthly performance for completed orders."""

    query = """
        SELECT
            strftime('%Y-%m', o.order_date) AS month,
            COUNT(DISTINCT o.order_id) AS total_orders,
            COALESCE(SUM(oi.quantity), 0) AS units_sold,
            COALESCE(SUM(oi.quantity * oi.unit_price), 0)
                AS revenue,
            COALESCE(SUM(oi.quantity * p.unit_cost), 0)
                AS cost
        FROM orders AS o
        JOIN order_items AS oi
            ON o.order_id = oi.order_id
        JOIN products AS p
            ON oi.product_id = p.product_id
        WHERE o.status = 'completed'
        GROUP BY strftime('%Y-%m', o.order_date)
        ORDER BY month
    """

    with closing(get_connection()) as connection:
        rows = connection.execute(query).fetchall()

    monthly_data = []

    for row in rows:
        revenue = row["revenue"]
        cost = row["cost"]

        monthly_data.append({
            "month": row["month"],
            "total_orders": row["total_orders"],
            "units_sold": row["units_sold"],
            "revenue": round(revenue, 2),
            "cost": round(cost, 2),
            "profit": round(revenue - cost, 2),
        })

    return monthly_data


def get_product_performance():
    """Rank products using completed orders only."""

    query = """
        SELECT
            p.product_name,
            p.category,
            COALESCE(s.units_sold, 0) AS units_sold,
            COALESCE(s.revenue, 0) AS revenue,
            COALESCE(s.profit, 0) AS profit
        FROM products AS p
        LEFT JOIN (
            SELECT
                oi.product_id,
                SUM(oi.quantity) AS units_sold,
                SUM(oi.quantity * oi.unit_price) AS revenue,
                SUM(
                    oi.quantity * (oi.unit_price - p.unit_cost)
                ) AS profit
            FROM order_items AS oi
            JOIN orders AS o
                ON oi.order_id = o.order_id
            JOIN products AS p
                ON oi.product_id = p.product_id
            WHERE o.status = 'completed'
            GROUP BY oi.product_id
        ) AS s
            ON p.product_id = s.product_id
        ORDER BY revenue DESC, p.product_name
    """

    with closing(get_connection()) as connection:
        rows = connection.execute(query).fetchall()

    return [
        {
            "product_name": row["product_name"],
            "category": row["category"],
            "units_sold": row["units_sold"],
            "revenue": round(row["revenue"], 2),
            "profit": round(row["profit"], 2),
        }
        for row in rows
    ]
