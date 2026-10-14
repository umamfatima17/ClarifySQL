"""Read-only schema discovery with bounded sample values."""

from contextlib import closing

from core.database import DATABASE_PATH, get_connection


def get_database_schema(include_sample_values=True):
    """Return table metadata and safe, bounded examples for low-cardinality columns."""
    if not DATABASE_PATH.exists():
        raise FileNotFoundError("ClarifySQL database does not exist.")

    schema = {}

    with closing(get_connection()) as connection:
        connection.execute("PRAGMA query_only = ON")

        tables = connection.execute(
            """SELECT name FROM sqlite_master
               WHERE type = 'table'
               AND name NOT LIKE 'sqlite_%'
               ORDER BY name"""
        ).fetchall()

        for table_row in tables:
            table_name = table_row["name"]
            quoted_table = '"' + table_name.replace('"', '""') + '"'

            column_rows = connection.execute(
                f"PRAGMA table_info({quoted_table})"
            ).fetchall()

            table_columns = []

            for column in column_rows:
                column_name = column["name"]
                column_type = (column["type"] or "").upper()
                item = {
                    "name": column_name,
                    "type": column["type"],
                    "not_null": bool(column["notnull"]),
                    "primary_key": bool(column["pk"]),
                }

                # Examples are useful for text filters such as category/status.
                # Avoid sampling numeric columns and high-cardinality text fields.
                if (
                    include_sample_values
                    and any(kind in column_type for kind in ("TEXT", "CHAR", "CLOB"))
                ):
                    quoted_column = '"' + column_name.replace('"', '""') + '"'
                    distinct_rows = connection.execute(
                        f"""SELECT DISTINCT {quoted_column}
                            FROM {quoted_table}
                            WHERE {quoted_column} IS NOT NULL
                            LIMIT 11"""
                    ).fetchall()

                    if len(distinct_rows) <= 10:
                        item["sample_values"] = [
                            str(row[0])[:100] for row in distinct_rows
                        ]

                table_columns.append(item)

            schema[table_name] = table_columns

    return schema
