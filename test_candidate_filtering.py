import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import sqlite3
from app import app
from database import get_matched_workers_for_job, is_profession_match

def run_tests():
    print("==================================================")
    print("TESTING PROFESSION-BASED CANDIDATE FILTERING")
    print("==================================================")

    app.config["TESTING"] = True
    client = app.test_client()

    # 1. Test is_profession_match directly for various professions
    print("\n[TEST 1] Testing is_profession_match function across trades...")
    assert is_profession_match("Driver", "Driver") is True
    assert is_profession_match("driver", "Driving") is True
    assert is_profession_match("Electrician", "Electrician") is True
    assert is_profession_match("Painter", "Painter") is True
    assert is_profession_match("Plumber", "Plumbing") is True
    assert is_profession_match("Mason", "Masonry") is True
    assert is_profession_match("Farm Worker", "Farming") is True
    assert is_profession_match("Helper", "Helper") is True

    # Negative matches
    assert is_profession_match("Electrician", "Driver") is False
    assert is_profession_match("Painter", "Driver") is False
    assert is_profession_match("Mason", "Driver") is False
    assert is_profession_match("Farming", "Electrician") is False
    assert is_profession_match("Helper", "Plumber") is False
    assert is_profession_match("Carpenter", "Electrician") is False
    print("✓ is_profession_match verified correctly for matching and non-matching professions!")

    # 2. Test get_matched_workers_for_job with Driver job (Job 3: Driver / Driving)
    print("\n[TEST 2] Testing Candidate Matcher with Driver Job...")
    driver_matches = get_matched_workers_for_job(3)
    print(f"Total candidates returned for Driver job (Job #3): {len(driver_matches)}")
    for c in driver_matches:
        print(f"  Candidate: {c['name']} | Profession: {c['skill']} | Match: {c['match_percentage']}%")
        assert is_profession_match(c["skill"], "Driver"), f"Non-driver candidate {c['name']} with skill {c['skill']} was found!"
    assert len(driver_matches) > 0, "Expected at least 1 driver candidate"
    print("✓ Strict Driver filtering verified: only Driver candidates returned!")

    # 3. Test get_matched_workers_for_job with Electrician job (Job 2: House Wiring / Electrician)
    print("\n[TEST 3] Testing Candidate Matcher with Electrician Job...")
    elec_matches = get_matched_workers_for_job(2)
    print(f"Total candidates returned for Electrician job (Job #2): {len(elec_matches)}")
    for c in elec_matches:
        print(f"  Candidate: {c['name']} | Profession: {c['skill']} | Match: {c['match_percentage']}%")
        assert is_profession_match(c["skill"], "Electrician"), f"Non-electrician candidate {c['name']} with skill {c['skill']} was found!"
    assert len(elec_matches) > 0, "Expected at least 1 electrician candidate"
    print("✓ Strict Electrician filtering verified: only Electrician candidates returned!")

    # 4. Test empty profession handling with a profession having no candidates (e.g. Carpenter)
    print("\n[TEST 4] Testing Empty Results Handling for Unmatched Profession...")
    # Create temporary carpenter job
    with sqlite3.connect("workconnect.db") as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO jobs (employer_id, title, skill_required, description, location, workers_needed, daily_wage, status, positions_remaining)
            VALUES (3, 'Furniture Making', 'Carpenter', 'Making chairs', 'Narasapur', 1, 800, 'Open', 1)
            """
        )
        carpenter_job_id = cur.lastrowid
        conn.commit()

    carp_matches = get_matched_workers_for_job(carpenter_job_id)
    print(f"Total candidates returned for Carpenter job (Job #{carpenter_job_id}): {len(carp_matches)}")
    assert len(carp_matches) == 0, f"Expected 0 carpenter candidates, got {len(carp_matches)}"
    print("✓ No alternative/unrelated candidates returned when no workers exist for profession!")

    # 5. Test Flask Employer Candidate Matcher UI & Dynamic Job Switching
    print("\n[TEST 5] Testing Candidate Matcher Web Route & Dynamic Job Selection...")
    # Login as employer Suresh
    with client.session_transaction() as sess:
        sess.clear()
    login_res = client.post("/login", data={
        "role": "employer",
        "email": "suresh.demo@example.com",
        "password": "password123"
    }, follow_redirects=True)
    assert login_res.status_code == 200

    # View candidate matcher for Driver job
    res_driver_page = client.get(f"/employer/candidate-matches?job_id=3")
    assert res_driver_page.status_code == 200
    html_driver = res_driver_page.get_data(as_text=True)
    assert "Active Job: Driver" in html_driver
    assert "Schedule Meeting" in html_driver
    # Thilak (Driver/Driving) must be present
    assert "Thilak" in html_driver
    # Ravi Kumar (Electrician) must NOT be in the matched candidate results
    # Check that Electrician is not present as a candidate badge
    assert "🛠️ <strong>Electrician</strong>" not in html_driver
    print("✓ Web UI for Driver job correctly shows Driver candidates and excludes Electricians!")

    # Switch dynamically to Electrician job (Job 2)
    res_elec_page = client.get(f"/employer/candidate-matches?job_id=2")
    assert res_elec_page.status_code == 200
    html_elec = res_elec_page.get_data(as_text=True)
    assert "Active Job: House Wiring" in html_elec
    assert "Schedule Meeting" in html_elec
    # Ravi Kumar (Electrician) must be present
    assert "Ravi Kumar" in html_elec
    # Driver candidate badge must NOT be in the matched candidate results
    assert "🛠️ <strong>Driver</strong>" not in html_elec
    assert "🛠️ <strong>Driving</strong>" not in html_elec
    print("✓ Web UI dynamically updates when switching to Electrician job!")

    # Switch to Carpenter job with no matching candidates
    res_carp_page = client.get(f"/employer/candidate-matches?job_id={carpenter_job_id}")
    assert res_carp_page.status_code == 200
    html_carp = res_carp_page.get_data(as_text=True)
    assert "No candidates found for this profession." in html_carp
    assert '<div class="candidate-card"' not in html_carp  # No candidate cards in body
    assert "🛠️ <strong>Driver</strong>" not in html_carp
    assert "🛠️ <strong>Electrician</strong>" not in html_carp
    print("✓ Web UI correctly displays 'No candidates found for this profession.' when empty!")

    # Cleanup carpenter job
    with sqlite3.connect("workconnect.db") as conn:
        conn.execute("DELETE FROM jobs WHERE id = ?", (carpenter_job_id,))
        conn.commit()

    # 6. Test Interview Modal Popup UI & Layout Order
    print("\n[TEST 6] Testing Interview Modal Popup UI & Form Fields...")
    res_modal_check = client.get(f"/employer/candidate-matches?job_id=3")
    html_modal = res_modal_check.get_data(as_text=True)

    # Check modal overlay and box styles
    assert ".modal-overlay {" in html_modal
    assert "position: fixed;" in html_modal
    assert ".modal-box {" in html_modal
    assert "max-width: 500px;" in html_modal
    assert "modal-close-btn" in html_modal

    # Check field labels and placeholders in order
    idx_date = html_modal.find("Meeting Date")
    idx_time = html_modal.find("Meeting Time")
    idx_venue = html_modal.find("Meeting Venue")
    idx_phone = html_modal.find("Meeting Phone Number")
    idx_notes = html_modal.find("Notes")
    idx_send_btn = html_modal.find("Send Meeting Request")
    idx_cancel_btn = html_modal.find("Cancel")

    assert idx_date != -1, "Meeting Date field missing"
    assert idx_time != -1, "Meeting Time field missing"
    assert idx_venue != -1, "Meeting Venue field missing"
    assert idx_phone != -1, "Meeting Phone Number field missing"
    assert idx_notes != -1, "Notes field missing"
    assert idx_send_btn != -1, "Send Meeting Request button missing"
    assert idx_cancel_btn != -1, "Cancel button missing"

    # Verify field ordering: Date -> Time -> Venue -> Phone -> Notes -> Send -> Cancel
    assert idx_date < idx_time < idx_venue < idx_phone < idx_notes < idx_send_btn < idx_cancel_btn, \
        "Field order mismatch! Expected: Date -> Time -> Venue -> Phone -> Notes -> Send -> Cancel"

    # Check placeholders
    assert 'placeholder="e.g., Site Office, Narasapur"' in html_modal
    assert 'placeholder="Enter phone number for phone meeting"' in html_modal
    print("✓ Meeting Modal Popup UI, layout, styling, and field order verified!")

    # 7. Test Submitting Meeting Request with Separate Venue & Phone
    print("\n[TEST 7] Testing Meeting Request Submission with Venue & Phone...")
    # Find Thilak's worker id
    with sqlite3.connect("workconnect.db") as conn:
        worker_row = conn.execute("SELECT id FROM workers WHERE skill IN ('Driver', 'Driving') LIMIT 1").fetchone()
        thilak_id = worker_row[0]

    post_iv_res = client.post("/employer/interviews/schedule", data={
        "job_id": 3,
        "application_id": 0,
        "worker_id": thilak_id,
        "interview_date": "2026-11-10",
        "interview_time": "14:00",
        "venue": "Narasapur Site Office",
        "phone": "9876543210",
        "notes": "Bring driving license",
        "return_to": "candidate_matches"
    }, follow_redirects=True)

    assert post_iv_res.status_code == 200
    html_after_post = post_iv_res.get_data(as_text=True)
    assert "Meeting scheduled successfully" in html_after_post
    print("✓ Meeting request submitted and success message rendered!")

    # Verify interview in DB
    with sqlite3.connect("workconnect.db") as conn:
        conn.row_factory = sqlite3.Row
        iv = conn.execute("SELECT * FROM interviews WHERE worker_id = ? ORDER BY id DESC LIMIT 1", (thilak_id,)).fetchone()
        assert iv is not None
        assert "Narasapur Site Office" in iv["location_or_link"]
        assert "9876543210" in iv["location_or_link"]
        assert iv["interview_date"] == "2026-11-10"
        assert iv["interview_time"] == "14:00"
        # Cleanup
        conn.execute("DELETE FROM interviews WHERE id = ?", (iv["id"],))
        conn.execute("DELETE FROM notifications WHERE user_id = ? AND title IN ('Interview Scheduled', 'Meeting Scheduled')", (thilak_id,))
        conn.commit()

    print("✓ Meeting database record and candidate linkage verified!")

    print("\n==================================================")
    print("ALL PROFESSION-BASED CANDIDATE FILTERING TESTS PASSED!")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
