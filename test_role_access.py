import sys
import os

# Ensure stdout handles UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app import app

def run_tests():
    print("==================================================")
    print("STARTING WORKCONNECT ROLE-BASED ACCESS CONTROL TESTS")
    print("==================================================")
    
    app.config["TESTING"] = True
    client = app.test_client()

    # ----------------------------------------------------
    # TEST 1: WORKER LOGIN & HOME PAGE VISIBILITY
    # ----------------------------------------------------
    print("\n[TEST 1] Worker Login & Home Page Visibility...")
    with client.session_transaction() as sess:
        sess.clear()

    login_resp = client.post("/login", data={
        "role": "worker",
        "email": "ramu@gmail.com",
        "password": "password123"
    }, follow_redirects=True)
    assert login_resp.status_code == 200, f"Login failed with status {login_resp.status_code}"
    
    # Access Home Page as Worker
    home_resp = client.get("/")
    assert home_resp.status_code == 200
    home_html = home_resp.get_data(as_text=True)

    # Worker Dashboard MUST be visible
    assert "Worker Dashboard" in home_html, "Worker Dashboard should be visible to logged-in worker"
    assert "/worker/dashboard" in home_html, "Worker dashboard link should be present"
    assert "Browse Jobs" in home_html, "Browse Jobs should be visible to worker"

    # Employer Dashboard & Employer Features MUST be hidden
    assert "Employer Dashboard" not in home_html, "Employer Dashboard MUST be hidden from worker"
    assert "/employer/dashboard" not in home_html, "Employer dashboard link MUST be hidden from worker"
    assert "/jobs/post" not in home_html, "Post a Job link MUST be hidden from worker"
    assert "Candidate Matcher" not in home_html, "Candidate Matcher MUST be hidden from worker"
    assert "/employer/candidate-matches" not in home_html, "Candidate Matcher link MUST be hidden from worker"
    print("✓ Test 1 PASSED: Worker sees Worker Dashboard and worker features; Employer Dashboard & features are completely hidden.")

    # ----------------------------------------------------
    # TEST 2: LOGOUT & EMPLOYER LOGIN & HOME PAGE VISIBILITY
    # ----------------------------------------------------
    print("\n[TEST 2] Logout & Employer Login & Home Page Visibility...")
    logout_resp = client.get("/logout", follow_redirects=True)
    assert logout_resp.status_code == 200

    login_resp = client.post("/login", data={
        "role": "employer",
        "email": "raju@gmail.com",
        "password": "password123"
    }, follow_redirects=True)
    assert login_resp.status_code == 200

    # Access Home Page as Employer
    home_resp = client.get("/")
    assert home_resp.status_code == 200
    home_html = home_resp.get_data(as_text=True)

    # Employer Dashboard MUST be visible
    assert "Employer Dashboard" in home_html, "Employer Dashboard should be visible to logged-in employer"
    assert "/employer/dashboard" in home_html, "Employer dashboard link should be present"
    assert "/jobs/post" in home_html, "Post a Job link should be present for employer"
    assert "Candidate Matcher" in home_html, "Candidate Matcher should be visible for employer"
    assert "/employer/candidate-matches" in home_html, "Candidate Matcher link should be present for employer"

    # Worker Dashboard & Worker-only cards MUST be hidden
    assert "Worker Dashboard" not in home_html, "Worker Dashboard MUST be hidden from employer"
    assert "/worker/dashboard" not in home_html, "Worker dashboard link MUST be hidden from employer"
    assert "trade-cards-gallery" not in home_html, "Worker trade pictures showcase should be hidden from employer"
    assert '<div class="voice-hero-banner">' not in home_html, "Worker voice registration hero banner should be hidden from employer"
    print("✓ Test 2 PASSED: Employer sees Employer Dashboard and employer features; Worker Dashboard & features are completely hidden.")

    # ----------------------------------------------------
    # TEST 3: WORKER ATTEMPTS TO ACCESS EMPLOYER-ONLY ROUTES
    # ----------------------------------------------------
    print("\n[TEST 3] Worker Account Accessing Employer-Only Routes (Expect Access Denied)...")
    # Log in as worker
    client.get("/logout", follow_redirects=True)
    client.post("/login", data={
        "role": "worker",
        "email": "ramu@gmail.com",
        "password": "password123"
    }, follow_redirects=True)

    employer_routes = [
        ("/employer/dashboard", "GET"),
        ("/employer/candidate-matches", "GET"),
        ("/jobs/post", "GET"),
        ("/employer/applications", "GET"),
        ("/employer/verify", "POST"),
        ("/employer/interviews/schedule", "POST"),
        ("/register/employer", "GET"),
        ("/register/employer", "POST")
    ]

    for route, method in employer_routes:
        if method == "GET":
            resp = client.get(route, follow_redirects=False)
        else:
            resp = client.post(route, data={"sample": "data"}, follow_redirects=False)

        assert resp.status_code in (302, 403), f"Route {route} [{method}] allowed worker access! Status: {resp.status_code}"
        assert resp.headers.get("Location") in ("/", "http://localhost/"), f"Route {route} did not redirect unauthorized worker to home. Redirected to: {resp.headers.get('Location')}"

        # Verify flash message when following redirect
        if method == "GET":
            follow_resp = client.get(route, follow_redirects=True)
            text = follow_resp.get_data(as_text=True)
            assert "Unauthorized" in text, f"Route {route} did not display Unauthorized message to worker"

    print("✓ Test 3 PASSED: All employer-only routes strictly denied access to worker account with redirect and unauthorized message.")

    # ----------------------------------------------------
    # TEST 4: EMPLOYER ATTEMPTS TO ACCESS WORKER-ONLY ROUTES
    # ----------------------------------------------------
    print("\n[TEST 4] Employer Account Accessing Worker-Only Routes (Expect Access Denied)...")
    # Log in as employer
    client.get("/logout", follow_redirects=True)
    client.post("/login", data={
        "role": "employer",
        "email": "raju@gmail.com",
        "password": "password123"
    }, follow_redirects=True)

    worker_routes = [
        ("/worker/dashboard", "GET"),
        ("/worker/profile/edit", "GET"),
        ("/worker/applications", "GET"),
        ("/jobs/1/apply", "GET"),
        ("/jobs/1/apply", "POST"),
        ("/jobs/1/save", "POST"),
        ("/jobs/1/unsave", "POST"),
        ("/register/worker", "GET"),
        ("/register/worker", "POST"),
        ("/register/worker/voice", "GET")
    ]

    for route, method in worker_routes:
        if method == "GET":
            resp = client.get(route, follow_redirects=False)
        else:
            resp = client.post(route, data={"sample": "data"}, follow_redirects=False)

        assert resp.status_code in (302, 403), f"Route {route} [{method}] allowed employer access! Status: {resp.status_code}"
        assert resp.headers.get("Location") in ("/", "http://localhost/"), f"Route {route} did not redirect unauthorized employer to home. Redirected to: {resp.headers.get('Location')}"

        # Verify flash message when following redirect
        if method == "GET":
            follow_resp = client.get(route, follow_redirects=True)
            text = follow_resp.get_data(as_text=True)
            assert "Unauthorized" in text, f"Route {route} did not display Unauthorized message to employer"

    print("✓ Test 4 PASSED: All worker-only routes strictly denied access to employer account with redirect and unauthorized message.")

    # ----------------------------------------------------
    # TEST 5: SHARED PAGES AND FEATURES WORK PROPERLY
    # ----------------------------------------------------
    print("\n[TEST 5] Shared Pages, Logout, and Language Switching...")
    # Public (unauthenticated) Home Page
    client.get("/logout", follow_redirects=True)
    guest_resp = client.get("/")
    assert guest_resp.status_code == 200
    guest_html = guest_resp.get_data(as_text=True)
    assert "Browse Jobs" in guest_html
    assert "Worker Portal" in guest_html
    assert "Employer Portal" in guest_html
    # Do not display both dashboard cards to the same user or unauthenticated
    assert "/worker/dashboard" not in guest_html
    assert "/employer/dashboard" not in guest_html

    # Public Browse Jobs
    browse_resp = client.get("/jobs")
    assert browse_resp.status_code == 200
    assert "Explore Jobs" in browse_resp.get_data(as_text=True)

    # Public Job Details
    job_resp = client.get("/jobs/1")
    assert job_resp.status_code == 200

    # Language Switcher
    lang_resp = client.get("/set-language/te", follow_redirects=True)
    assert lang_resp.status_code == 200
    assert "తెలుగు" in lang_resp.get_data(as_text=True)

    # Switch back to English
    client.get("/set-language/en", follow_redirects=True)
    print("✓ Test 5 PASSED: Shared pages (Home, Jobs, Job Details, Language Switching) continue to work seamlessly.")

    # ----------------------------------------------------
    # TEST 6: ROLE SWITCHING ACROSS MULTIPLE LOGINS
    # ----------------------------------------------------
    print("\n[TEST 6] Role Switching Across Multiple Logins...")
    for cycle in range(3):
        # 1. Login Worker
        client.post("/login", data={"role": "worker", "email": "ramu@gmail.com", "password": "password123"}, follow_redirects=True)
        h1 = client.get("/").get_data(as_text=True)
        assert "Worker Dashboard" in h1 and "Employer Dashboard" not in h1, f"Cycle {cycle}: Worker view failed"

        # 2. Logout
        client.get("/logout", follow_redirects=True)

        # 3. Login Employer
        client.post("/login", data={"role": "employer", "email": "raju@gmail.com", "password": "password123"}, follow_redirects=True)
        h2 = client.get("/").get_data(as_text=True)
        assert "Employer Dashboard" in h2 and "Worker Dashboard" not in h2, f"Cycle {cycle}: Employer view failed"

        # 4. Logout
        client.get("/logout", follow_redirects=True)

    print("✓ Test 6 PASSED: Logging out and logging in with another role updates navigation and dashboard visibility correctly every time.")

    # ----------------------------------------------------
    # TEST 7: REFRESHING PAGE PERSISTENCE
    # ----------------------------------------------------
    print("\n[TEST 7] Refreshing Page Does Not Cause Wrong Dashboard to Appear...")
    # Worker refresh
    client.post("/login", data={"role": "worker", "email": "ramu@gmail.com", "password": "password123"}, follow_redirects=True)
    for _ in range(5):
        r = client.get("/")
        html = r.get_data(as_text=True)
        assert "Worker Dashboard" in html and "Employer Dashboard" not in html, "Refreshing caused wrong dashboard in worker session!"

    # Employer refresh
    client.get("/logout", follow_redirects=True)
    client.post("/login", data={"role": "employer", "email": "raju@gmail.com", "password": "password123"}, follow_redirects=True)
    for _ in range(5):
        r = client.get("/")
        html = r.get_data(as_text=True)
        assert "Employer Dashboard" in html and "Worker Dashboard" not in html, "Refreshing caused wrong dashboard in employer session!"

    print("✓ Test 7 PASSED: Refreshing the page does not cause the wrong dashboard to appear.")

    print("\n==================================================")
    print("ALL 7 ROLE-BASED ACCESS CONTROL TESTS PASSED SUCCESSFULLY!")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
