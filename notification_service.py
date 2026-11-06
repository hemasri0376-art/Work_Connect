"""
WorkConnect Notification Service
Provides decoupled, modular notification management for WorkConnect.

Supports:
- Job posting notifications for registered workers
- Extensible notification types (Job Posted, Application Status, Employer Viewed, Interview Scheduled)
- Deduplication prevention for job events
- Unread counts, mark as read, and mark all as read
- Friendly relative time formatting for notifications
"""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

# Connect to database via shared DATABASE_NAME from database module
from database import DATABASE_NAME, get_job_by_id, get_all_workers


class NotificationType:
    """Supported notification types (extensible for future features)."""
    JOB_POSTED = "JOB_POSTED"
    APPLICATION_STATUS = "APPLICATION_STATUS"
    EMPLOYER_VIEWED = "EMPLOYER_VIEWED"
    INTERVIEW_SCHEDULED = "INTERVIEW_SCHEDULED"


def format_relative_time(timestamp_str):
    """
    Format a database timestamp string into a friendly relative time (e.g. 'Just now', '5m ago').
    Gracefully handles various datetime formats.
    """
    if not timestamp_str:
        return "Recently"

    dt = None
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d",
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(str(timestamp_str).strip(), fmt)
            break
        except (ValueError, TypeError):
            continue

    if not dt:
        return str(timestamp_str)

    # SQLite CURRENT_TIMESTAMP is UTC
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    delta = now_utc - dt
    total_seconds = int(delta.total_seconds())

    if total_seconds < 0:
        return "Just now"
    if total_seconds < 45:
        return "Just now"
    if total_seconds < 3600:
        minutes = max(1, total_seconds // 60)
        return f"{minutes}m ago"
    if total_seconds < 86400:
        hours = total_seconds // 3600
        return f"{hours}h ago"
    if total_seconds < 604800:
        days = total_seconds // 86400
        return f"{days}d ago"

    # Beyond a week, show date
    return dt.strftime("%b %d, %Y")


def notify_workers_new_job(job_id):
    """
    Trigger notifications for all workers when a new job is successfully posted.
    Ensures:
    - The job exists in database.
    - Duplicate notifications for the same job event are prevented.
    - All active workers receive an unread notification with rich metadata.
    """
    if not job_id:
        return 0

    job = get_job_by_id(job_id)
    if not job:
        return 0

    workers = get_all_workers()
    if not workers:
        return 0

    created_count = 0
    with sqlite3.connect(DATABASE_NAME) as connection:
        cursor = connection.cursor()

        # Check existing notifications for this job to prevent duplicates
        cursor.execute(
            """
            SELECT user_id FROM notifications 
            WHERE job_id = ? AND notification_type = ? AND user_role = 'worker'
            """,
            (job_id, NotificationType.JOB_POSTED)
        )
        already_notified_worker_ids = {r[0] for r in cursor.fetchall()}

        employer_name = job.get("employer_name") or "An employer"
        job_title = job.get("title") or "New Job"
        location = job.get("location") or "Local"
        wage = job.get("daily_wage", 0)

        title = "A new job has been posted!"
        message = f"'{job_title}' posted by {employer_name} in {location} (₹{wage}/day)."
        link = f"/jobs/{job_id}"

        for worker in workers:
            w_id = worker["id"]
            if w_id in already_notified_worker_ids:
                continue

            cursor.execute(
                """
                INSERT INTO notifications 
                (user_role, user_id, title, message, link, notification_type, job_id, company_name, job_title, location, is_read)
                VALUES ('worker', ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                """,
                (
                    w_id,
                    title,
                    message,
                    link,
                    NotificationType.JOB_POSTED,
                    job_id,
                    employer_name,
                    job_title,
                    location
                )
            )
            created_count += 1

        connection.commit()

    return created_count


def get_worker_notifications(worker_id, unread_only=False):
    """
    Retrieve notifications for a worker in reverse chronological order (newest first).
    Enriches records with friendly time display and fallback metadata.
    """
    if not worker_id:
        return []

    with sqlite3.connect(DATABASE_NAME) as connection:
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()

        query = """
            SELECT id, user_role, user_id, title, message, link, 
                   notification_type, job_id, company_name, job_title, location,
                   is_read, created_at
            FROM notifications
            WHERE user_role = 'worker' AND user_id = ?
        """
        params = [worker_id]
        if unread_only:
            query += " AND is_read = 0"
        query += " ORDER BY id DESC LIMIT 50"

        rows = cursor.execute(query, params).fetchall()
        result = []
        for r in rows:
            item = dict(r)
            # Enrich relative time
            item["time_display"] = format_relative_time(item.get("created_at"))

            # Fallback metadata if not directly populated in legacy records
            if not item.get("job_title") and item.get("title"):
                item["job_title"] = item.get("title")
            if not item.get("company_name"):
                item["company_name"] = "WorkConnect Partner"
            if not item.get("location"):
                item["location"] = "On-site"
            if not item.get("link"):
                if item.get("job_id"):
                    item["link"] = f"/jobs/{item['job_id']}"
                else:
                    item["link"] = "/worker/dashboard"

            result.append(item)

        return result


def mark_notification_as_read(notification_id, user_id, user_role="worker"):
    """Mark a single notification as read for the user."""
    with sqlite3.connect(DATABASE_NAME) as connection:
        connection.execute(
            "UPDATE notifications SET is_read = 1 WHERE id = ? AND user_role = ? AND user_id = ?",
            (notification_id, user_role, user_id)
        )
        connection.commit()
    return True


def mark_all_as_read(user_id, user_role="worker"):
    """Mark all notifications as read for the user."""
    with sqlite3.connect(DATABASE_NAME) as connection:
        connection.execute(
            "UPDATE notifications SET is_read = 1 WHERE user_role = ? AND user_id = ?",
            (user_role, user_id)
        )
        connection.commit()
    return True


def get_unread_count(user_id, user_role="worker"):
    """Return unread notification count for the user."""
    if not user_id:
        return 0
    with sqlite3.connect(DATABASE_NAME) as connection:
        row = connection.execute(
            "SELECT COUNT(*) FROM notifications WHERE user_role = ? AND user_id = ? AND is_read = 0",
            (user_role, user_id)
        ).fetchone()
        return row[0] if row else 0

