
import sqlite3
from database import DATABASE_NAME

with sqlite3.connect(DATABASE_NAME) as connection:
    rows = connection.execute("""
        SELECT
            a.id,
            w.name,
            j.title,
            a.status,
            a.applied_at
        FROM applications AS a
        JOIN workers AS w ON a.worker_id = w.id
        JOIN jobs AS j ON a.job_id = j.id
    """).fetchall()

    if rows:
        for row in rows:
            print("Application ID:", row[0])
            print("Worker:", row[1])
            print("Job:", row[2])
            print("Status:", row[3])
            print("Applied at:", row[4])
            print("-" * 30)
    else:
        print("No applications found.")
