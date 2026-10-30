import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
import sqlite3
from database import (
    initialize_database,
    compute_match_score,
    get_all_jobs,
    get_job_by_id,
    get_all_workers,
    get_worker_by_email,
    get_employer_by_email,
    get_applications_by_employer,
    get_applications_by_worker,
    update_application_status,
    recalculate_job_positions,
    get_matched_workers_for_job,
    DATABASE_NAME
)

def run_tests():
    print("==================================================")
    print(" WORKCONNECT COMPREHENSIVE WORKFLOW & MATCH TEST  ")
    print("==================================================")

    # 1. Test Database Initialization (Phase 04)
    print("\n[TEST 1] Initializing Database & Verifying Schema...")
    initialize_database()

    with sqlite3.connect(DATABASE_NAME) as conn:
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        print("Existing Tables:", tables)
        assert "workers" in tables, "workers table missing"
        assert "employers" in tables, "employers table missing"
        assert "jobs" in tables, "jobs table missing"
        assert "applications" in tables, "applications table missing"

        # Check required columns for intelligent matching & core workflow
        worker_cols = [c[1] for c in conn.execute("PRAGMA table_info(workers)").fetchall()]
        assert "availability" in worker_cols, "availability column missing in workers"
        assert "rating" in worker_cols, "rating column missing in workers"

        job_cols = [c[1] for c in conn.execute("PRAGMA table_info(jobs)").fetchall()]
        assert "positions_remaining" in job_cols, "positions_remaining missing in jobs"

    print("[PASS] Schema verification passed!")

    # 2. Test Intelligent Match Score Calculation (Phase 06)
    print("\n[TEST 2] Testing Intelligent Matching Algorithm...")
    worker_sample = {
        "name": "Test Worker",
        "email": "testworker@example.com",
        "skill": "Electrician",
        "location": "Narasapur",
        "experience": 4,
        "wage": 650,
        "availability": "Immediate",
        "rating": 4.9
    }
    job_sample = {
        "title": "House Electrician Needed",
        "skill_required": "Electrician",
        "location": "Narasapur",
        "daily_wage": 700,
        "workers_needed": 2,
        "description": "Wiring work"
    }

    match = compute_match_score(worker_sample, job_sample)
    print(f"Computed Score: {match['score']}/100 ({match['percentage']}%) - Level: {match['level']}")
    print("Breakdown:", match["breakdown"])

    assert match["breakdown"]["skills"]["score"] == 35.0, "Expected exact skill match (35 pts)"
    assert match["breakdown"]["location"]["score"] == 20.0, "Expected exact location match (20 pts)"
    assert match["breakdown"]["wage"]["score"] == 15.0, "Expected within budget wage match (15 pts)"
    assert match["breakdown"]["availability"]["score"] == 10.0, "Expected immediate availability (10 pts)"
    assert match["score"] >= 90.0, "Score should be >= 90% for high compatibility"
    print("[PASS] Intelligent matching calculation passed!")

    # 3. Test Employer Job Post & Remaining Positions Tracking (Phase 05)
    print("\n[TEST 3] Testing Core Workflow: Job Posting & Position Tracking...")
    with sqlite3.connect(DATABASE_NAME) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        # Ensure test employer exists
        emp = conn.execute("SELECT id FROM employers WHERE email = 'test_emp@example.com'").fetchone()
        if not emp:
            cur = conn.execute(
                "INSERT INTO employers (name, email, employer_type, location) VALUES ('Test Builder', 'test_emp@example.com', 'Construction', 'Narasapur')"
            )
            emp_id = cur.lastrowid
        else:
            emp_id = emp[0]

        # Post a requirement needing 2 workers
        cur = conn.execute(
            """
            INSERT INTO jobs (employer_id, title, skill_required, description, location, workers_needed, positions_remaining, daily_wage, status)
            VALUES (?, 'Solar Panel Installation', 'Electrician', 'Install rooftop panels', 'Narasapur', 2, 2, 800, 'Open')
            """,
            (emp_id,)
        )
        test_job_id = cur.lastrowid
        conn.commit()

    job = get_job_by_id(test_job_id)
    assert job["workers_needed"] == 2
    assert job["positions_remaining"] == 2
    assert job["status"] == "Open"
    print(f"[PASS] Job #{test_job_id} created with 2 positions needed, remaining: {job['positions_remaining']}")

    # 4. Test Worker Application & Employer Review (Phase 05: Shortlist, Confirm, Reject)
    print("\n[TEST 4] Testing Application Workflow & Real-time Capacity Update...")
    with sqlite3.connect(DATABASE_NAME) as conn:
        # Pick 2 existing workers or create test workers
        w1 = conn.execute("SELECT id, email FROM workers WHERE email = 'ravi.demo@example.com'").fetchone()
        w2 = conn.execute("SELECT id, email FROM workers WHERE email = 'raghu@gmail.com'").fetchone()

        # Submit applications
        conn.execute("INSERT OR IGNORE INTO applications (worker_id, job_id, status) VALUES (?, ?, 'Pending')", (w1[0], test_job_id))
        conn.execute("INSERT OR IGNORE INTO applications (worker_id, job_id, status) VALUES (?, ?, 'Pending')", (w2[0], test_job_id))
        conn.commit()

        apps = conn.execute("SELECT id, worker_id, status FROM applications WHERE job_id = ?", (test_job_id,)).fetchall()
        app1_id = apps[0][0]
        app2_id = apps[1][0]

    # Employer retrieves applications sorted by match score
    employer_apps = get_applications_by_employer("test_emp@example.com", job_id=test_job_id)
    print(f"Retrieved {len(employer_apps)} applications for job #{test_job_id}")
    for ea in employer_apps:
        print(f"  Applicant: {ea['worker_name']} | Match: {ea['match_percentage']}% | Status: {ea['application_status']}")

    # 4A. Shortlist application 1
    print("Action: Shortlist application 1...")
    ok, msg = update_application_status(app1_id, "Shortlisted", emp_id)
    assert ok, msg
    job_state = get_job_by_id(test_job_id)
    assert job_state["positions_remaining"] == 2, "Shortlisting should not consume position"
    print(f"[PASS] Shortlisted! Remaining positions still {job_state['positions_remaining']}/2")

    # 4B. Confirm application 1
    print("Action: Confirm application 1...")
    ok, msg = update_application_status(app1_id, "Confirmed", emp_id)
    assert ok, msg
    job_state = get_job_by_id(test_job_id)
    assert job_state["positions_remaining"] == 1, "Confirming should reduce remaining positions to 1"
    assert job_state["status"] == "Open", "Job should still be Open"
    print(f"[PASS] Application 1 Confirmed! Remaining positions: {job_state['positions_remaining']}/2")

    # 4C. Confirm application 2 (should fill the job!)
    print("Action: Confirm application 2...")
    ok, msg = update_application_status(app2_id, "Confirmed", emp_id)
    assert ok, msg
    job_state = get_job_by_id(test_job_id)
    assert job_state["positions_remaining"] == 0, "Remaining positions should now be 0"
    assert job_state["status"] == "Filled", "Job status should automatically become 'Filled'"
    print(f"[PASS] Application 2 Confirmed! Remaining: {job_state['positions_remaining']}/2, Job Status: {job_state['status']}")

    # 4D. Reject application 2 (should reopen position!)
    print("Action: Reject application 2 to restore vacancy...")
    ok, msg = update_application_status(app2_id, "Rejected", emp_id)
    assert ok, msg
    job_state = get_job_by_id(test_job_id)
    assert job_state["positions_remaining"] == 1, "Remaining positions should increase back to 1"
    assert job_state["status"] == "Open", "Job status should automatically reopen to 'Open'"
    print(f"[PASS] Position restored! Remaining: {job_state['positions_remaining']}/2, Job Status: {job_state['status']}")

    # 5. Test Candidate Matcher (Phase 06)
    print("\n[TEST 5] Testing Intelligent Worker Recommendation Engine for Job...")
    recommendations = get_matched_workers_for_job(test_job_id)
    print(f"Total Workers Scored for Job #{test_job_id}: {len(recommendations)}")
    for r in recommendations[:3]:
        print(f"  Worker: {r['name']} | Match: {r['match_percentage']}% ({r['match_level']}) | Skill: {r['skill']}")
    assert len(recommendations) > 0, "Expected recommendations"
    assert recommendations[0]["match_score"] >= recommendations[-1]["match_score"], "Recommendations must be sorted descending"
    print("[PASS] Recommendations sorted correctly by match score!")

    # Cleanup test job
    with sqlite3.connect(DATABASE_NAME) as conn:
        conn.execute("DELETE FROM applications WHERE job_id = ?", (test_job_id,))
        conn.execute("DELETE FROM jobs WHERE id = ?", (test_job_id,))
        conn.commit()

    print("\n==================================================")
    print(" ALL WORKFLOW & MATCHING TESTS PASSED PERFECTLY!  ")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
