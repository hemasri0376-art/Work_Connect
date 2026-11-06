import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import sqlite3
from app import app
from database import get_worker_by_email

def test_newly_registered_worker():
    app.config["TESTING"] = True
    client = app.test_client()

    test_email = "newworker_test@example.com"
    with sqlite3.connect("workconnect.db") as conn:
        conn.execute("DELETE FROM workers WHERE email = ?", (test_email,))
        conn.commit()

    # 1. Register new worker
    resp = client.post("/register/worker", data={
        "name": "Kalyan Test",
        "email": test_email,
        "password": "password123",
        "confirm_password": "password123",
        "skill": "Electrician",
        "location": "Vijayawada",
        "experience": "3",
        "wage": "750",
        "availability": "Immediate"
    }, follow_redirects=True)

    assert resp.status_code == 200, f"Registration failed with status {resp.status_code}"

    # 2. Check DB
    worker = get_worker_by_email(test_email)
    assert worker is not None, "Worker not found in DB"
    print(f"Worker rating in DB: {worker['rating']}")
    assert worker["rating"] is None, f"Expected rating to be None, got {worker['rating']}"

    # 3. Check Worker Dashboard
    dash_resp = client.get("/worker/dashboard")
    assert dash_resp.status_code == 200, f"Dashboard failed with status {dash_resp.status_code}"
    html = dash_resp.get_data(as_text=True)

    assert "4.8" not in html, "Found 4.8 in dashboard HTML!"
    assert "4.8/5.0" not in html, "Found 4.8/5.0 in dashboard HTML!"
    assert "/5.0" not in html, "Found /5.0 in dashboard HTML!"
    assert "Kalyan Test" in html, "Worker name missing in dashboard"
    assert "Electrician" in html, "Worker skill missing in dashboard"
    assert "Vijayawada" in html, "Worker location missing in dashboard"
    assert "750" in html, "Worker wage missing in dashboard"
    assert "Immediate" in html, "Worker availability missing in dashboard"

    # Also test Voice Registration flow
    with client.session_transaction() as sess:
        sess.clear()
    voice_email = "voice_worker@example.com"
    with sqlite3.connect("workconnect.db") as conn:
        conn.execute("DELETE FROM workers WHERE email = ?", (voice_email,))
        conn.commit()

    voice_resp = client.post("/register/worker", data={
        "name": "Lakshmi Voice",
        "email": voice_email,
        "password": "password123",
        "skill": "Farming",
        "location": "Narasapur",
        "experience": "2",
        "wage": "600"
    }, follow_redirects=True)
    assert voice_resp.status_code == 200
    v_worker = get_worker_by_email(voice_email)
    assert v_worker["rating"] is None, "Voice worker rating should be None"

    v_dash = client.get("/worker/dashboard")
    v_html = v_dash.get_data(as_text=True)
    assert "4.8" not in v_html
    assert "/5.0" not in v_html
    assert "Lakshmi Voice" in v_html
    assert "Farming" in v_html
    assert "Narasapur" in v_html

    with sqlite3.connect("workconnect.db") as conn:
        conn.execute("DELETE FROM workers WHERE email = ?", (voice_email,))
        conn.commit()

    # Also test an existing worker logging in (e.g. Ramu)
    with client.session_transaction() as sess:
        sess.clear()
    
    login_resp = client.post("/login", data={
        "role": "worker",
        "email": "ramu@gmail.com",
        "password": "password123"
    }, follow_redirects=True)
    assert login_resp.status_code == 200

    dash_ramu = client.get("/worker/dashboard")
    html_ramu = dash_ramu.get_data(as_text=True)
    # Even if existing worker in DB had 4.8, the dashboard profile card does not display the rating
    assert "⭐ 4.8/5.0" not in html_ramu
    assert "/5.0" not in html_ramu
    assert "Ramu" in html_ramu

    # Cleanup test worker
    with sqlite3.connect("workconnect.db") as conn:
        conn.execute("DELETE FROM workers WHERE email = ?", (test_email,))
        conn.commit()

    print("\n✓ Newly registered worker test PASSED: No default rating on dashboard, all profile details present and correctly formatted!")

if __name__ == "__main__":
    test_newly_registered_worker()
