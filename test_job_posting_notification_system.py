"""
Comprehensive Test Suite for WorkConnect Job Posting Notification System.

Verifies:
1. Database schema and migration for notifications table
2. Employer successfully posts a job and notification is triggered
3. Registered workers receive the notification with job title, company name, location, and time
4. Deduplication: duplicate notifications are prevented for the same job event
5. Reverse chronological ordering of notifications (newest first)
6. Worker dashboard renders notification bell icon, unread count badge, and dropdown panel
7. Job details page (/jobs/<id>) renders correct job information
8. Opening job with ?notif_id=<id> marks notification as read
9. API endpoint /api/notifications/read/<id> marks notification as read and updates count
10. API endpoint /api/notifications/read-all marks all notifications as read and resets count to 0
11. Empty state verification when user has no notifications
"""

import sys
import sqlite3
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app import app
from database import (
    DATABASE_NAME,
    initialize_database,
    get_job_by_id,
    get_all_workers,
    get_worker_by_email,
    get_employer_by_email,
    get_notifications,
    get_unread_notifications_count,
    mark_notification_as_read,
    mark_all_notifications_as_read
)
from notification_service import (
    NotificationType,
    notify_workers_new_job,
    get_worker_notifications,
    format_relative_time
)


def run_tests():
    print("==================================================================")
    print(" WORKCONNECT JOB POSTING NOTIFICATION SYSTEM - VERIFICATION SUITE ")
    print("==================================================================")

    # 1. Initialize DB and Verify Schema
    print("\n[TEST 1] Verifying Database Schema for Notifications...")
    initialize_database()
    with sqlite3.connect(DATABASE_NAME) as conn:
        cols = [c[1] for c in conn.execute("PRAGMA table_info(notifications)").fetchall()]
        for req_col in ["notification_type", "job_id", "company_name", "job_title", "location", "is_read", "link"]:
            assert req_col in cols, f"Column '{req_col}' missing from notifications table!"
    print("✓ Schema columns verified successfully!")

    # 2. Setup Test Client & Test Accounts
    client = app.test_client()

    emp = get_employer_by_email("suresh.demo@example.com")
    assert emp is not None, "Employer suresh.demo@example.com not found!"
    worker = get_worker_by_email("ravi.demo@example.com")
    assert worker is not None, "Worker ravi.demo@example.com not found!"

    # 3. Clean any existing notifications for our test job to start clean
    with sqlite3.connect(DATABASE_NAME) as conn:
        conn.execute("DELETE FROM notifications WHERE title LIKE '%Test Notification Job%'")
        conn.commit()

    initial_worker_notifs = get_notifications("worker", worker["id"])
    initial_unread = get_unread_notifications_count("worker", worker["id"])
    print(f"✓ Initial worker state: {len(initial_worker_notifs)} notifications, {initial_unread} unread.")

    # 4. Employer Posts a New Job via Flask Client
    print("\n[TEST 2] Testing Employer Job Posting & Notification Trigger...")
    with client.session_transaction() as sess:
        sess["user_id"] = emp["id"]
        sess["role"] = "employer"
        sess["email"] = emp["email"]
        sess["name"] = emp["name"]

    job_title = "Test Notification Job - Solar Specialist"
    post_res = client.post("/jobs/post", data={
        "title": job_title,
        "skill_required": "Electrician",
        "description": "Install residential solar systems with full safety equipment provided.",
        "location": "Narasapur Rural",
        "workers_needed": 3,
        "daily_wage": 750
    }, follow_redirects=True)

    assert post_res.status_code == 200, f"Job posting failed with status {post_res.status_code}"

    # Verify job was created in DB
    with sqlite3.connect(DATABASE_NAME) as conn:
        conn.row_factory = sqlite3.Row
        job_row = conn.execute("SELECT * FROM jobs WHERE title = ? ORDER BY id DESC LIMIT 1", (job_title,)).fetchone()
        assert job_row is not None, "Posted job not found in database!"
        new_job_id = job_row["id"]

    print(f"✓ Job '{job_title}' posted successfully with Job ID #{new_job_id}!")

    # 5. Verify Worker Received Notification
    print("\n[TEST 3] Verifying Worker Received the Job Notification...")
    worker_notifs = get_notifications("worker", worker["id"])
    matching_notifs = [n for n in worker_notifs if n.get("job_id") == new_job_id]
    assert len(matching_notifs) == 1, f"Expected 1 notification for job #{new_job_id}, found {len(matching_notifs)}!"

    notif = matching_notifs[0]
    assert notif["title"] == "A new job has been posted!"
    assert job_title in notif["message"] or job_title in (notif.get("job_title") or "")
    assert notif["company_name"] == emp["name"]
    assert notif["location"] == "Narasapur Rural"
    assert notif["link"] == f"/jobs/{new_job_id}"
    assert notif["is_read"] == 0
    assert notif["notification_type"] == NotificationType.JOB_POSTED

    new_unread = get_unread_notifications_count("worker", worker["id"])
    assert new_unread == initial_unread + 1, f"Unread count expected {initial_unread + 1}, got {new_unread}!"
    print(f"✓ Worker received notification #{notif['id']}: '{notif['title']}' for '{notif['job_title']}' by '{notif['company_name']}'.")
    print(f"✓ Unread count correctly increased to {new_unread}!")

    # 6. Deduplication Test: Triggering again for same job MUST NOT duplicate
    print("\n[TEST 4] Testing Deduplication Prevention...")
    duplicate_count = notify_workers_new_job(new_job_id)
    assert duplicate_count == 0, f"Expected 0 notifications created on duplicate trigger, got {duplicate_count}!"

    worker_notifs_after = get_notifications("worker", worker["id"])
    matching_after = [n for n in worker_notifs_after if n.get("job_id") == new_job_id]
    assert len(matching_after) == 1, "Duplicate notification was created!"
    print("✓ Deduplication successfully prevented duplicate notifications for the same job!")

    # 7. Reverse Chronological Ordering
    print("\n[TEST 5] Testing Reverse Chronological Ordering...")
    all_worker_notifs = get_worker_notifications(worker["id"])
    assert len(all_worker_notifs) >= 1
    # Newest job notification should be at the very top (index 0)
    assert all_worker_notifs[0]["job_id"] == new_job_id
    assert all_worker_notifs[0]["id"] >= all_worker_notifs[-1]["id"]
    print("✓ Notifications properly ordered in reverse chronological order (newest first)!")

    # 8. Worker Dashboard Rendering (Navbar Bell, Count Badge, Dropdown Panel)
    print("\n[TEST 6] Testing Worker Dashboard Rendering & Dropdown Panel...")
    with client.session_transaction() as sess:
        sess["user_id"] = worker["id"]
        sess["role"] = "worker"
        sess["email"] = worker["email"]
        sess["name"] = worker["name"]

    dash_res = client.get("/worker/dashboard")
    assert dash_res.status_code == 200
    html = dash_res.data.decode("utf-8")

    assert 'id="notif-bell-btn"' in html, "Notification bell button missing from navbar!"
    assert 'class="notif-count"' in html, "Notification count badge missing!"
    assert str(new_unread) in html, f"Unread count {new_unread} missing from navbar badge!"
    assert 'id="notif-dropdown-panel"' in html, "Notification dropdown panel missing from HTML!"
    assert 'A new job has been posted!' in html, "Notification title missing from dropdown!"
    assert job_title in html, "Job title missing from dropdown notifications!"
    assert emp["name"] in html, "Company name missing from dropdown notifications!"
    assert 'View Job' in html, "'View Job' button missing from notifications!"
    assert 'Mark as read' in html, "'Mark as read' button missing from unread notifications!"
    assert '✓ Mark all read' in html, "'Mark all read' action missing!"
    print("✓ Worker dashboard renders bell icon, unread count badge, and clean dropdown panel!")

    # 9. Dedicated Job Details Page (/jobs/<id>)
    print("\n[TEST 7] Testing Job Details Page Navigation & Auto-Read...")
    job_view_res = client.get(f"/jobs/{new_job_id}?notif_id={notif['id']}")
    assert job_view_res.status_code == 200
    job_html = job_view_res.data.decode("utf-8")

    assert job_title in job_html, "Job title not found on job details page!"
    assert emp["name"] in job_html, "Employer name not found on job details page!"
    assert "Narasapur Rural" in job_html, "Location not found on job details page!"
    assert "₹750" in job_html, "Daily wage not found on job details page!"
    assert "3 positions left" in job_html, "Positions remaining not found on job details page!"

    # Verify opening with ?notif_id marked it as read
    notif_after_click = [n for n in get_notifications("worker", worker["id"]) if n["id"] == notif["id"]][0]
    assert notif_after_click["is_read"] == 1, "Notification was not marked as read after clicking View Job!"
    print("✓ Job details page rendered all specifications correctly and marked notification as read!")

    # 10. API: Mark Single Notification Read & Unread Count Update
    print("\n[TEST 8] Testing API Read Notification & Count Updates...")
    # Create another test notification
    from database import create_notification
    create_notification("worker", worker["id"], "A new job has been posted!", "Another test job", f"/jobs/{new_job_id}",
                        job_id=new_job_id, company_name="ABC Ltd", job_title="Helper Needed", location="Eluru")
    unread_before = get_unread_notifications_count("worker", worker["id"])
    assert unread_before > 0

    latest_notif = get_notifications("worker", worker["id"], unread_only=True)[0]
    api_read_res = client.post(f"/api/notifications/read/{latest_notif['id']}")
    assert api_read_res.status_code == 200
    data = api_read_res.get_json()
    assert data["success"] is True
    assert data["unread_count"] == unread_before - 1

    unread_after = get_unread_notifications_count("worker", worker["id"])
    assert unread_after == unread_before - 1
    print("✓ Single notification read via API succeeded and unread count decremented!")

    # 11. API: Mark All As Read
    print("\n[TEST 9] Testing API Mark All As Read...")
    # Add a couple of unread notifications
    create_notification("worker", worker["id"], "A new job has been posted!", "Job 1", f"/jobs/{new_job_id}")
    create_notification("worker", worker["id"], "A new job has been posted!", "Job 2", f"/jobs/{new_job_id}")
    assert get_unread_notifications_count("worker", worker["id"]) >= 2

    api_read_all_res = client.post("/api/notifications/read-all")
    assert api_read_all_res.status_code == 200
    all_data = api_read_all_res.get_json()
    assert all_data["success"] is True
    assert all_data["unread_count"] == 0

    final_unread = get_unread_notifications_count("worker", worker["id"])
    assert final_unread == 0, f"Expected 0 unread notifications, got {final_unread}!"
    print("✓ Mark all as read via API succeeded and unread count reset to 0!")

    # 12. Friendly Relative Time Formatting
    print("\n[TEST 10] Testing Friendly Relative Time Formatting...")
    assert format_relative_time(None) == "Recently"
    from datetime import datetime, timezone, timedelta
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    assert format_relative_time(now_str) == "Just now"
    ten_min_ago = (datetime.now(timezone.utc) - timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")
    assert format_relative_time(ten_min_ago) == "10m ago"
    two_hours_ago = (datetime.now(timezone.utc) - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
    assert format_relative_time(two_hours_ago) == "2h ago"
    print("✓ Relative time formatting verified!")

    # 13. Empty State Verification
    print("\n[TEST 11] Testing Empty Notification State...")
    # New user with no notifications
    with sqlite3.connect(DATABASE_NAME) as conn:
        conn.execute("DELETE FROM notifications WHERE user_role = 'worker' AND user_id = 999999")
        conn.commit()
    empty_notifs = get_notifications("worker", 999999)
    assert len(empty_notifs) == 0
    assert get_unread_notifications_count("worker", 999999) == 0
    print("✓ Empty state returns zero notifications and zero unread count!")

    print("\n==================================================================")
    print(" ALL JOB POSTING NOTIFICATION SYSTEM TESTS PASSED SUCCESSFULLY! ")
    print("==================================================================")


if __name__ == "__main__":
    run_tests()
