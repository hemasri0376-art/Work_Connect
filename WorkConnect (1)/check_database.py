
import sqlite3
from database import DATABASE_NAME

with sqlite3.connect(DATABASE_NAME) as connection:
    connection.row_factory = sqlite3.Row

    for table in ("workers", "employers"):
        rows = connection.execute(
            f"SELECT * FROM {table} ORDER BY id"
        ).fetchall()

        print(f"\n--- {table.upper()} ---")
        print(f"Total records: {len(rows)}")

        for row in rows:
            print(dict(row))
