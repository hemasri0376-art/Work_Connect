import sqlite3
from flask import Flask, render_template, request, redirect, url_for
from database import (
    DATABASE_NAME,
    initialize_database,
    compute_match_score,
    get_all_jobs,
    get_job_by_id,
    get_worker_by_email,
    get_worker_by_id,
    get_employer_by_email,
    get_applications_by_employer,
    get_applications_by_worker,
    update_application_status,
    get_matched_workers_for_job,
    recalculate_job_positions
)

app = Flask(__name__)

# Initialize database schema and migrate existing data
initialize_database()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/register/worker", methods=["GET", "POST"])
def worker_register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        skill = request.form.get("skill", "").strip()
        location = request.form.get("location", "").strip()
        availability = request.form.get("availability", "Immediate").strip()

        try:
            experience = int(request.form.get("experience", "0"))
            wage = int(request.form.get("wage", "0"))
            rating = float(request.form.get("rating", "4.8"))
        except ValueError:
            return "Experience, wage, and rating must be valid numbers.", 400

        if not all([name, email, skill, location]):
            return "Please complete all required fields.", 400

        if experience < 0 or experience > 60 or wage < 0:
            return "Please enter a valid experience and wage.", 400

        rating = min(5.0, max(1.0, rating))

        try:
            with sqlite3.connect(DATABASE_NAME) as connection:
                connection.execute(
                    """
                    INSERT INTO workers
                    (name, email, skill, location, experience, wage, availability, rating)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (name, email, skill, location, experience, wage, availability, rating)
                )

            return render_template(
                "index.html",
                banner_message=f"Worker profile for '{name}' registered successfully! You can now browse matched jobs."
            )

        except sqlite3.IntegrityError:
            return """
                <h2>Registration not completed</h2>
                <p>This email is already registered as a worker on WorkConnect.</p>
                <a href="/register/worker">Try again</a>
            """, 400

    return render_template("worker_register.html")


@app.route("/register/employer", methods=["GET", "POST"])
def employer_register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        employer_type = request.form.get("type", "").strip()
        location = request.form.get("location", "").strip()

        if not all([name, email, employer_type, location]):
            return "Please complete all required fields.", 400

        try:
            with sqlite3.connect(DATABASE_NAME) as connection:
                connection.execute(
                    """
                    INSERT INTO employers
                    (name, email, employer_type, location)
                    VALUES (?, ?, ?, ?)
                    """,
                    (name, email, employer_type, location)
                )

            return render_template(
                "index.html",
                banner_message=f"Employer '{name}' registered successfully! You can now post jobs."
            )

        except sqlite3.IntegrityError:
            return """
                <h2>Registration not completed</h2>
                <p>This email is already registered as an employer.</p>
                <a href="/register/employer">Try again</a>
            """, 400

    return render_template("employer_register.html")


@app.route("/jobs/post", methods=["GET", "POST"])
def post_job():
    if request.method == "POST":
        employer_email = request.form.get("employer_email", "").strip().lower()
        title = request.form.get("title", "").strip()
        skill = request.form.get("skill_required", "").strip()
        description = request.form.get("description", "").strip()
        location = request.form.get("location", "").strip()

        try:
            workers_needed = int(request.form.get("workers_needed", "0"))
            daily_wage = int(request.form.get("daily_wage", "-1"))
        except ValueError:
            return "Workers needed and daily wage must be valid whole numbers.", 400

        if not all([employer_email, title, skill, description, location]):
            return "Please complete all required fields.", 400

        if not (1 <= workers_needed <= 10000) or daily_wage < 0:
            return "Please enter a valid number of workers and wage.", 400

        try:
            with sqlite3.connect(DATABASE_NAME) as connection:
                connection.execute("PRAGMA foreign_keys = ON")
                employer = connection.execute(
                    "SELECT id FROM employers WHERE email = ?", (employer_email,)
                ).fetchone()

                if employer is None:
                    return (
                        "Employer not found. Please register first using the employer registration page."
                    ), 404

                cursor = connection.cursor()
                cursor.execute(
                    """
                    INSERT INTO jobs
                    (employer_id, title, skill_required, description,
                     location, workers_needed, positions_remaining, daily_wage, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Open')
                    """,
                    (
                        employer[0], title, skill, description,
                        location, workers_needed, workers_needed, daily_wage
                    )
                )
                connection.commit()

            return render_template(
                "index.html",
                banner_message=f"Job requirement '{title}' posted successfully with {workers_needed} positions open!"
            )

        except sqlite3.IntegrityError:
            return "Could not save the job. Please check the submitted details.", 400

    return render_template("job_post.html")


@app.route("/jobs")
def browse_jobs():
    """
    Search and browse jobs (Phase 05 & 06):
    - Search by keyword, skill, location, max wage.
    - Intelligent match score personalized for a worker (entered via email).
    - Sort by match score, newest, wage, or remaining positions.
    """
    search_query = request.args.get("q", "").strip()
    skill_filter = request.args.get("skill", "").strip()
    location_filter = request.args.get("location", "").strip()
    max_wage = request.args.get("max_wage", "").strip()
    worker_email = request.args.get("worker_email", "").strip().lower()
    sort_by = request.args.get("sort", "match" if worker_email else "newest").strip()

    jobs = get_all_jobs(
        status_filter="Open",
        search_query=search_query,
        skill_filter=skill_filter,
        location_filter=location_filter,
        max_wage=max_wage,
        worker_email=worker_email,
        sort_by=sort_by
    )

    worker = get_worker_by_email(worker_email) if worker_email else None

    # Retrieve unique skills and locations for quick filter pills
    with sqlite3.connect(DATABASE_NAME) as connection:
        skills = [r[0] for r in connection.execute("SELECT DISTINCT skill_required FROM jobs WHERE status = 'Open' ORDER BY skill_required").fetchall()]
        locations = [r[0] for r in connection.execute("SELECT DISTINCT location FROM jobs WHERE status = 'Open' ORDER BY location").fetchall()]

    return render_template(
        "browse_jobs.html",
        jobs=jobs,
        worker=worker,
        worker_email=worker_email,
        search_query=search_query,
        skill_filter=skill_filter,
        location_filter=location_filter,
        max_wage=max_wage,
        sort_by=sort_by,
        available_skills=skills,
        available_locations=locations
    )


@app.route("/jobs/<int:job_id>/apply", methods=["GET", "POST"])
def apply_job(job_id):
    job = get_job_by_id(job_id)
    if job is None:
        return "Job not found.", 404

    # Calculate live remaining positions
    job_stats = recalculate_job_positions(job_id)
    if job_stats and job_stats["positions_remaining"] <= 0:
        return "This job has already been filled. No open positions remain.", 400

    match_info = None
    worker_email_query = request.args.get("worker_email", "").strip().lower()
    if worker_email_query:
        worker = get_worker_by_email(worker_email_query)
        if worker:
            match_info = compute_match_score(worker, job)

    if request.method == "POST":
        worker_email = request.form.get("worker_email", "").strip().lower()
        message = request.form.get("message", "").strip()

        if not worker_email:
            return "Please provide your registered worker email.", 400

        worker = get_worker_by_email(worker_email)
        if worker is None:
            return (
                "Worker not found with this email. Please register as a worker first "
                "before applying."
            ), 404

        # Verify job still has open capacity
        recalc = recalculate_job_positions(job_id)
        if recalc and recalc["positions_remaining"] <= 0:
            return "Sorry, all positions for this job were just filled.", 400

        try:
            with sqlite3.connect(DATABASE_NAME) as connection:
                connection.execute("PRAGMA foreign_keys = ON")
                connection.execute(
                    """
                    INSERT INTO applications (worker_id, job_id, status)
                    VALUES (?, ?, 'Pending')
                    """,
                    (worker["id"], job["id"])
                )

            return render_template(
                "index.html",
                banner_message=f"Application for '{job['title']}' submitted successfully! Track it in your Worker Dashboard."
            )

        except sqlite3.IntegrityError:
            return """
                <h2>Application Already Submitted</h2>
                <p>You have already applied for this job opportunity.</p>
                <a href="/jobs">Return to Browse Jobs</a>
            """, 400

    return render_template(
        "apply_job.html",
        job=job,
        worker_email=worker_email_query,
        match_info=match_info
    )


@app.route("/employer/applications", methods=["GET", "POST"])
def employer_applications():
    """
    Employer Dashboard (Phase 05 & 06):
    - Employers review applications for their jobs.
    - Shortlist, confirm, or reject applications.
    - Remaining positions update accurately!
    - Intelligent match score calculated and sorted by score.
    """
    applications = []
    error = None
    message = None
    employer_email = request.args.get("employer_email", "").strip().lower()
    selected_status = request.args.get("status_filter", "All").strip()
    selected_job_id = request.args.get("job_id", "").strip()
    sort_by = request.args.get("sort_by", "match").strip()

    if request.method == "POST":
        employer_email = request.form.get("employer_email", "").strip().lower()
        action = request.form.get("action", "view").strip()
        selected_status = request.form.get("status_filter", "All").strip()
        sort_by = request.form.get("sort_by", "match").strip()

        if not employer_email:
            error = "Please enter your registered employer email."
        elif action == "update_status":
            try:
                application_id = int(request.form.get("application_id", ""))
                new_status = request.form.get("status", "").strip()
            except (TypeError, ValueError):
                application_id = None
                new_status = ""

            employer = get_employer_by_email(employer_email)
            if not employer:
                error = "Employer not found. Please register first."
            else:
                success, msg = update_application_status(application_id, new_status, employer["id"])
                if success:
                    message = msg
                else:
                    error = msg

    employer_jobs = []
    if employer_email:
        employer = get_employer_by_email(employer_email)
        if employer:
            job_filter_int = int(selected_job_id) if selected_job_id.isdigit() else None
            applications = get_applications_by_employer(
                employer_email=employer_email,
                job_id=job_filter_int,
                status_filter=selected_status if selected_status != "All" else None,
                sort_by=sort_by
            )
            with sqlite3.connect(DATABASE_NAME) as connection:
                connection.row_factory = sqlite3.Row
                employer_jobs = [dict(r) for r in connection.execute(
                    "SELECT id, title, skill_required, workers_needed, positions_remaining, status FROM jobs WHERE employer_id = ? ORDER BY id DESC",
                    (employer["id"],)
                ).fetchall()]
        elif not error:
            error = "Employer not found. Please enter your registered email address."

    return render_template(
        "employer_applications.html",
        applications=applications,
        error=error,
        message=message,
        employer_email=employer_email,
        employer_jobs=employer_jobs,
        selected_status=selected_status,
        selected_job_id=selected_job_id,
        sort_by=sort_by
    )


@app.route("/employer/candidate-matches", methods=["GET", "POST"])
def candidate_matches():
    """
    Intelligent Worker Recommendation Engine (Phase 06):
    Employers can select one of their job postings and see all registered
    workers ranked by match score to discover top suitable talent.
    """
    employer_email = request.args.get("employer_email", "").strip().lower()
    job_id_param = request.args.get("job_id", "").strip()

    if request.method == "POST":
        employer_email = request.form.get("employer_email", "").strip().lower()
        job_id_param = request.form.get("job_id", "").strip()

    employer = get_employer_by_email(employer_email) if employer_email else None
    employer_jobs = []
    selected_job = None
    matched_workers = []

    if employer:
        with sqlite3.connect(DATABASE_NAME) as connection:
            connection.row_factory = sqlite3.Row
            employer_jobs = [dict(r) for r in connection.execute(
                "SELECT * FROM jobs WHERE employer_id = ? ORDER BY id DESC",
                (employer["id"],)
            ).fetchall()]

        if not job_id_param and employer_jobs:
            selected_job = employer_jobs[0]
        elif job_id_param and job_id_param.isdigit():
            selected_job = get_job_by_id(int(job_id_param))

        if selected_job:
            matched_workers = get_matched_workers_for_job(selected_job["id"], min_score=0)

    return render_template(
        "candidate_matches.html",
        employer=employer,
        employer_email=employer_email,
        employer_jobs=employer_jobs,
        selected_job=selected_job,
        matched_workers=matched_workers
    )


@app.route("/worker/applications", methods=["GET", "POST"])
def worker_applications():
    """
    Worker Dashboard (Phase 05 & 06):
    - Track all submitted applications.
    - View live status: Pending, Shortlisted, Confirmed, Rejected.
    - View Intelligent Match Score breakdown.
    """
    applications = []
    error = None
    worker_email = request.args.get("worker_email", "").strip().lower()
    sort_by = request.args.get("sort_by", "match").strip()

    if request.method == "POST":
        worker_email = request.form.get("worker_email", "").strip().lower()

    if worker_email:
        worker = get_worker_by_email(worker_email)
        if worker is None:
            error = "Worker not found. Please enter the email you used during worker registration."
        else:
            applications = get_applications_by_worker(worker_email, sort_by=sort_by)

    return render_template(
        "worker_applications.html",
        applications=applications,
        error=error,
        worker_email=worker_email,
        sort_by=sort_by
    )


if __name__ == "__main__":
    app.run(debug=True)
