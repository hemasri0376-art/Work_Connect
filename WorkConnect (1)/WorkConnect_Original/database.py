import sqlite3
from pathlib import Path

# Store the database beside this Python file
DATABASE_NAME = Path(__file__).resolve().parent / "workconnect.db"


def initialize_database():
    """
    Initialize SQLite database tables and apply schema updates if needed.
    Supports:
    - Phase 04: Users, worker profiles, requirements (jobs), applications tables.
    - Phase 05: Core workflow (post requirements, search & apply, shortlist/confirm/reject, remaining positions).
    - Phase 06: Intelligent matching (skills, availability, location, experience, wage, rating).
    """
    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON")

    # Table for worker profiles
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS workers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            skill TEXT NOT NULL,
            location TEXT NOT NULL,
            experience INTEGER NOT NULL CHECK (experience >= 0),
            wage INTEGER NOT NULL CHECK (wage >= 0),
            availability TEXT NOT NULL DEFAULT 'Immediate',
            rating REAL NOT NULL DEFAULT 4.8,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Table for employer registrations
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            employer_type TEXT NOT NULL,
            location TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Table for job postings / requirements
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employer_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            skill_required TEXT NOT NULL,
            description TEXT NOT NULL,
            location TEXT NOT NULL,
            workers_needed INTEGER NOT NULL CHECK (workers_needed > 0),
            positions_remaining INTEGER NOT NULL DEFAULT 1,
            daily_wage INTEGER NOT NULL CHECK (daily_wage >= 0),
            status TEXT NOT NULL DEFAULT 'Open',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employer_id) REFERENCES employers(id)
        )
    """)

    # Table for worker job applications
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_id INTEGER NOT NULL,
            job_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',
            applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (worker_id) REFERENCES workers(id),
            FOREIGN KEY (job_id) REFERENCES jobs(id),
            UNIQUE (worker_id, job_id)
        )
    """)
    # Security migration: store password hashes, never plaintext passwords.
    worker_cols = {
        column[1]
        for column in cursor.execute("PRAGMA table_info(workers)").fetchall()
    }
    if "password_hash" not in worker_cols:
        cursor.execute("ALTER TABLE workers ADD COLUMN password_hash TEXT")

    employer_cols = {
        column[1]
        for column in cursor.execute("PRAGMA table_info(employers)").fetchall()
    }
    if "password_hash" not in employer_cols:
        cursor.execute("ALTER TABLE employers ADD COLUMN password_hash TEXT")

    # -------------------------------------------------------------
    # Schema Migration / Consistency check for existing databases
    # -------------------------------------------------------------
    # 1. Ensure workers has availability and rating
    worker_cols = [c[1] for c in cursor.execute("PRAGMA table_info(workers)").fetchall()]
    if "availability" not in worker_cols:
        cursor.execute("ALTER TABLE workers ADD COLUMN availability TEXT NOT NULL DEFAULT 'Immediate'")
    if "rating" not in worker_cols:
        cursor.execute("ALTER TABLE workers ADD COLUMN rating REAL NOT NULL DEFAULT 4.8")

    # 2. Ensure jobs has positions_remaining
    job_cols = [c[1] for c in cursor.execute("PRAGMA table_info(jobs)").fetchall()]
    if "positions_remaining" not in job_cols:
        cursor.execute("ALTER TABLE jobs ADD COLUMN positions_remaining INTEGER NOT NULL DEFAULT 1")

    # 3. Standardize historical 'Accepted' applications to 'Confirmed'
    cursor.execute("UPDATE applications SET status = 'Confirmed' WHERE status = 'Accepted'")

    # 4. Synchronize positions_remaining for all existing jobs
    cursor.execute("SELECT id, workers_needed FROM jobs")
    all_jobs = cursor.fetchall()
    for job_id, needed in all_jobs:
        confirmed_count = cursor.execute(
            "SELECT COUNT(*) FROM applications WHERE job_id = ? AND status = 'Confirmed'",
            (job_id,)
        ).fetchone()[0]
        remaining = max(0, needed - confirmed_count)
        new_status = 'Filled' if remaining == 0 else 'Open'
        cursor.execute(
            "UPDATE jobs SET positions_remaining = ?, status = ? WHERE id = ?",
            (remaining, new_status, job_id)
        )

    connection.commit()
    connection.close()

    print("WorkConnect database initialized and synchronized successfully!")


def compute_match_score(worker, job):
    """
    Intelligent Matching Engine (Phase 06):
    Calculates a 0-100 match score based on 6 key dimensions:
    1. Skill match (up to 35 pts) - required skill vs worker skill
    2. Location match (up to 20 pts) - proximity and locality match
    3. Experience match (up to 15 pts) - years of experience
    4. Wage compatibility (up to 15 pts) - worker expected wage vs job daily wage
    5. Availability match (up to 10 pts) - worker readiness
    6. Rating score (up to 5 pts) - worker track record & feedback
    """
    w = dict(worker) if hasattr(worker, "keys") else worker
    j = dict(job) if hasattr(job, "keys") else job

    # 1. Skill Match (Max: 35 pts)
    w_skill = (w.get("skill") or "").strip().lower()
    j_skill = (j.get("skill_required") or "").strip().lower()
    j_title = (j.get("title") or "").strip().lower()
    j_desc = (j.get("description") or "").strip().lower()

    if w_skill and j_skill:
        if w_skill == j_skill:
            skill_score = 35.0
            skill_desc = "Exact skill match"
        elif w_skill in j_skill or j_skill in w_skill:
            skill_score = 25.0
            skill_desc = "Strong skill overlap"
        elif w_skill in j_title or w_skill in j_desc:
            skill_score = 18.0
            skill_desc = "Skill mentioned in job description"
        else:
            skill_score = 0.0
            skill_desc = "Skill mismatch"
    else:
        skill_score = 10.0
        skill_desc = "General skill"

    # 2. Location Match (Max: 20 pts)
    w_loc = (w.get("location") or "").strip().lower()
    j_loc = (j.get("location") or "").strip().lower()

    if w_loc and j_loc:
        if w_loc == j_loc:
            loc_score = 20.0
            loc_desc = "Exact location match"
        elif w_loc in j_loc or j_loc in w_loc:
            loc_score = 12.0
            loc_desc = "Same region / neighboring area"
        else:
            loc_score = 0.0
            loc_desc = "Different location"
    else:
        loc_score = 5.0
        loc_desc = "Location flexible"

    # 3. Experience Match (Max: 15 pts)
    try:
        exp = int(w.get("experience") or 0)
    except (TypeError, ValueError):
        exp = 0

    if exp >= 5:
        exp_score = 15.0
        exp_desc = f"Expert ({exp} yrs exp)"
    elif exp >= 3:
        exp_score = 13.0
        exp_desc = f"Experienced ({exp} yrs exp)"
    elif exp >= 1:
        exp_score = 10.0
        exp_desc = f"Competent ({exp} yrs exp)"
    else:
        exp_score = 6.0
        exp_desc = "Entry-level / Fresher"

    # 4. Wage Compatibility (Max: 15 pts)
    try:
        w_wage = int(w.get("wage") or 0)
        j_wage = int(j.get("daily_wage") or 0)
    except (TypeError, ValueError):
        w_wage = 0
        j_wage = 0

    if j_wage > 0 and w_wage > 0:
        if w_wage <= j_wage:
            wage_score = 15.0
            wage_desc = f"Within budget (₹{w_wage} ≤ ₹{j_wage})"
        elif w_wage <= j_wage * 1.2:
            wage_score = 8.0
            wage_desc = f"Close to budget (within 20%)"
        else:
            wage_score = 2.0
            wage_desc = f"Expected wage exceeds offer (₹{w_wage} > ₹{j_wage})"
    else:
        wage_score = 10.0
        wage_desc = "Flexible wage"

    # 5. Availability (Max: 10 pts)
    avail = str(w.get("availability") or "Immediate").strip().lower()
    if "immediate" in avail or "available" in avail:
        avail_score = 10.0
        avail_desc = "Immediately available"
    elif "week" in avail or "within" in avail:
        avail_score = 7.0
        avail_desc = "Available within 1 week"
    elif "part" in avail:
        avail_score = 6.0
        avail_desc = "Part-time availability"
    else:
        avail_score = 5.0
        avail_desc = "Standard availability"

    # 6. Rating (Max: 5 pts)
    try:
        rating = float(w.get("rating") or 4.8)
    except (TypeError, ValueError):
        rating = 4.5

    rating = min(5.0, max(1.0, rating))
    rating_score = round((rating / 5.0) * 5.0, 1)
    rating_desc = f"{rating:.1f}/5.0 rating"

    # Total Score Calculation
    total_score = round(skill_score + loc_score + exp_score + wage_score + avail_score + rating_score, 1)
    percentage = int(min(100, max(0, round(total_score))))

    if percentage >= 85:
        level = "Excellent Match"
        badge_class = "match-excellent"
    elif percentage >= 70:
        level = "Good Match"
        badge_class = "match-good"
    elif percentage >= 50:
        level = "Moderate Match"
        badge_class = "match-moderate"
    else:
        level = "Low Match"
        badge_class = "match-low"

    return {
        "score": total_score,
        "percentage": percentage,
        "level": level,
        "badge_class": badge_class,
        "breakdown": {
            "skills": {"score": skill_score, "max": 35, "desc": skill_desc},
            "location": {"score": loc_score, "max": 20, "desc": loc_desc},
            "experience": {"score": exp_score, "max": 15, "desc": exp_desc, "years": exp},
            "wage": {"score": wage_score, "max": 15, "desc": wage_desc, "worker_wage": w_wage, "job_wage": j_wage},
            "availability": {"score": avail_score, "max": 10, "desc": avail_desc},
            "rating": {"score": rating_score, "max": 5, "desc": rating_desc, "rating": rating}
        }
    }


def recalculate_job_positions(job_id, connection=None):
    """
    Recalculate remaining positions for a job based on Confirmed applications.
    Updates the jobs table:
    - positions_remaining = max(0, workers_needed - count_confirmed)
    - status = 'Filled' if positions_remaining == 0 else 'Open'
    """
    close_conn = False
    if connection is None:
        connection = sqlite3.connect(DATABASE_NAME)
        close_conn = True

    try:
        cursor = connection.cursor()
        job_row = cursor.execute(
            "SELECT workers_needed FROM jobs WHERE id = ?", (job_id,)
        ).fetchone()

        if not job_row:
            return None

        needed = job_row[0]
        confirmed_count = cursor.execute(
            """
            SELECT COUNT(*) FROM applications
            WHERE job_id = ? AND status IN ('Confirmed', 'Accepted')
            """,
            (job_id,)
        ).fetchone()[0]

        remaining = max(0, needed - confirmed_count)
        new_status = 'Filled' if remaining == 0 else 'Open'

        cursor.execute(
            """
            UPDATE jobs
            SET positions_remaining = ?, status = ?
            WHERE id = ?
            """,
            (remaining, new_status, job_id)
        )
        connection.commit()

        return {
            "job_id": job_id,
            "workers_needed": needed,
            "confirmed_count": confirmed_count,
            "positions_remaining": remaining,
            "status": new_status
        }
    finally:
        if close_conn:
            connection.close()


def get_all_workers():
    """Return all workers as a list of dicts."""
    with sqlite3.connect(DATABASE_NAME) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute("SELECT * FROM workers ORDER BY id").fetchall()
        return [dict(r) for r in rows]


def get_worker_by_email(email):
    """Return a worker by email (or None)."""
    with sqlite3.connect(DATABASE_NAME) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            "SELECT * FROM workers WHERE email = ?", (email.strip().lower(),)
        ).fetchone()
        return dict(row) if row else None


def get_worker_by_id(worker_id):
    """Return a worker by ID (or None)."""
    with sqlite3.connect(DATABASE_NAME) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            "SELECT * FROM workers WHERE id = ?", (worker_id,)
        ).fetchone()
        return dict(row) if row else None


def get_all_employers():
    """Return all employers as a list of dicts."""
    with sqlite3.connect(DATABASE_NAME) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute("SELECT * FROM employers ORDER BY id").fetchall()
        return [dict(r) for r in rows]


def get_employer_by_email(email):
    """Return an employer by email (or None)."""
    with sqlite3.connect(DATABASE_NAME) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            "SELECT * FROM employers WHERE email = ?", (email.strip().lower(),)
        ).fetchone()
        return dict(row) if row else None


def get_job_by_id(job_id):
    """Return a single job by ID with employer details (or None)."""
    with sqlite3.connect(DATABASE_NAME) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            """
            SELECT jobs.*, employers.name AS employer_name
            FROM jobs
            JOIN employers ON jobs.employer_id = employers.id
            WHERE jobs.id = ?
            """,
            (job_id,),
        ).fetchone()
        return dict(row) if row else None


def get_all_jobs(status_filter="Open", search_query=None, skill_filter=None,
                 location_filter=None, max_wage=None, worker_email=None, sort_by=None):
    """
    Return jobs matching filters, with intelligent matching if worker_email is provided.
    Supports search by keyword, skill, location, wage, and intelligent match sorting.
    """
    with sqlite3.connect(DATABASE_NAME) as connection:
        connection.row_factory = sqlite3.Row

        query = """
            SELECT
                jobs.*,
                employers.name AS employer_name,
                (SELECT COUNT(*) FROM applications WHERE job_id = jobs.id AND status IN ('Confirmed', 'Accepted')) AS confirmed_count
            FROM jobs
            JOIN employers ON jobs.employer_id = employers.id
            WHERE 1=1
        """
        params = []

        if status_filter:
            query += " AND jobs.status = ?"
            params.append(status_filter)

        if skill_filter and skill_filter.strip():
            query += " AND LOWER(jobs.skill_required) LIKE ?"
            params.append(f"%{skill_filter.strip().lower()}%")

        if location_filter and location_filter.strip():
            query += " AND LOWER(jobs.location) LIKE ?"
            params.append(f"%{location_filter.strip().lower()}%")

        if max_wage:
            try:
                max_wage_val = int(max_wage)
                query += " AND jobs.daily_wage <= ?"
                params.append(max_wage_val)
            except ValueError:
                pass

        if search_query and search_query.strip():
            search_term = f"%{search_query.strip().lower()}%"
            query += " AND (LOWER(jobs.title) LIKE ? OR LOWER(jobs.description) LIKE ? OR LOWER(jobs.skill_required) LIKE ? OR LOWER(jobs.location) LIKE ?)"
            params.extend([search_term, search_term, search_term, search_term])

        query += " ORDER BY jobs.id DESC"
        raw_jobs = [dict(r) for r in connection.execute(query, params).fetchall()]

    # If worker is specified, compute match score for every job
    worker = None
    if worker_email:
        worker = get_worker_by_email(worker_email)

    for j in raw_jobs:
        if "positions_remaining" not in j or j["positions_remaining"] is None:
            j["positions_remaining"] = max(0, j["workers_needed"] - j["confirmed_count"])

        if worker:
            match = compute_match_score(worker, j)
            j["match_score"] = match["score"]
            j["match_percentage"] = match["percentage"]
            j["match_level"] = match["level"]
            j["match_badge_class"] = match["badge_class"]
            j["match_breakdown"] = match["breakdown"]
        else:
            j["match_score"] = None
            j["match_percentage"] = None
            j["match_level"] = None
            j["match_badge_class"] = None
            j["match_breakdown"] = None

    # Sorting
    if sort_by == "match" and worker:
        raw_jobs.sort(key=lambda x: (x["match_score"] or 0), reverse=True)
    elif sort_by == "wage_desc":
        raw_jobs.sort(key=lambda x: x["daily_wage"], reverse=True)
    elif sort_by == "wage_asc":
        raw_jobs.sort(key=lambda x: x["daily_wage"])
    elif sort_by == "positions":
        raw_jobs.sort(key=lambda x: x["positions_remaining"], reverse=True)

    return raw_jobs


def get_applications_by_employer(employer_email, job_id=None, status_filter=None, sort_by="match"):
    """
    Return all applications for jobs posted by a given employer.
    Attaches full intelligent match scores and detailed applicant and job info.
    Sorted by match score descending by default.
    """
    with sqlite3.connect(DATABASE_NAME) as connection:
        connection.row_factory = sqlite3.Row
        employer = connection.execute(
            "SELECT id FROM employers WHERE email = ?", (employer_email.strip().lower(),)
        ).fetchone()

        if employer is None:
            return []

        query = """
            SELECT
                applications.id AS application_id,
                applications.status AS application_status,
                applications.applied_at AS applied_at,
                workers.id AS worker_id,
                workers.name AS worker_name,
                workers.email AS worker_email,
                workers.skill AS worker_skill,
                workers.location AS worker_location,
                workers.experience AS worker_experience,
                workers.wage AS worker_wage,
                workers.availability AS worker_availability,
                workers.rating AS worker_rating,
                jobs.id AS job_id,
                jobs.title AS job_title,
                jobs.skill_required AS job_skill,
                jobs.location AS job_location,
                jobs.daily_wage AS job_daily_wage,
                jobs.workers_needed AS job_workers_needed,
                jobs.positions_remaining AS job_positions_remaining,
                jobs.status AS job_status,
                (SELECT COUNT(*) FROM applications WHERE job_id = jobs.id AND status IN ('Confirmed', 'Accepted')) AS confirmed_count
            FROM applications
            JOIN workers ON applications.worker_id = workers.id
            JOIN jobs ON applications.job_id = jobs.id
            WHERE jobs.employer_id = ?
        """
        params = [employer["id"]]

        if job_id:
            query += " AND jobs.id = ?"
            params.append(job_id)

        if status_filter and status_filter != "All":
            query += " AND applications.status = ?"
            params.append(status_filter)

        query += " ORDER BY applications.applied_at DESC"
        rows = [dict(r) for r in connection.execute(query, params).fetchall()]

    for app in rows:
        worker_dict = {
            "skill": app["worker_skill"],
            "location": app["worker_location"],
            "experience": app["worker_experience"],
            "wage": app["worker_wage"],
            "availability": app.get("worker_availability", "Immediate"),
            "rating": app.get("worker_rating", 4.8)
        }
        job_dict = {
            "title": app["job_title"],
            "skill_required": app["job_skill"],
            "location": app["job_location"],
            "daily_wage": app["job_daily_wage"],
            "workers_needed": app["job_workers_needed"],
            "description": ""
        }
        match = compute_match_score(worker_dict, job_dict)
        app["match_score"] = match["score"]
        app["match_percentage"] = match["percentage"]
        app["match_level"] = match["level"]
        app["match_badge_class"] = match["badge_class"]
        app["match_breakdown"] = match["breakdown"]

    if sort_by == "match":
        rows.sort(key=lambda x: (x["match_score"], x["applied_at"]), reverse=True)
    elif sort_by == "date":
        rows.sort(key=lambda x: x["applied_at"], reverse=True)

    return rows


def get_applications_by_worker(worker_email, sort_by="date"):
    """
    Return all applications for a given worker with intelligent match scores.
    """
    with sqlite3.connect(DATABASE_NAME) as connection:
        connection.row_factory = sqlite3.Row
        worker = connection.execute(
            "SELECT * FROM workers WHERE email = ?", (worker_email.strip().lower(),)
        ).fetchone()

        if worker is None:
            return []

        worker_dict = dict(worker)

        query = """
            SELECT
                applications.id AS application_id,
                applications.status AS application_status,
                applications.applied_at AS applied_at,
                jobs.id AS job_id,
                jobs.title AS job_title,
                jobs.skill_required AS job_skill,
                jobs.location AS job_location,
                jobs.daily_wage AS daily_wage,
                jobs.workers_needed AS workers_needed,
                jobs.positions_remaining AS positions_remaining,
                jobs.status AS job_status,
                employers.name AS employer_name
            FROM applications
            JOIN jobs ON applications.job_id = jobs.id
            JOIN employers ON jobs.employer_id = employers.id
            WHERE applications.worker_id = ?
            ORDER BY applications.applied_at DESC
        """
        rows = [dict(r) for r in connection.execute(query, (worker["id"],)).fetchall()]

    for app in rows:
        job_dict = {
            "title": app["job_title"],
            "skill_required": app["job_skill"],
            "location": app["job_location"],
            "daily_wage": app["daily_wage"],
            "workers_needed": app["workers_needed"],
            "description": ""
        }
        match = compute_match_score(worker_dict, job_dict)
        app["match_score"] = match["score"]
        app["match_percentage"] = match["percentage"]
        app["match_level"] = match["level"]
        app["match_badge_class"] = match["badge_class"]
        app["match_breakdown"] = match["breakdown"]

    if sort_by == "match":
        rows.sort(key=lambda x: (x["match_score"], x["applied_at"]), reverse=True)

    return rows


def update_application_status(application_id, new_status, employer_id):
    """
    Update application status (Pending, Shortlisted, Confirmed, Rejected).
    Also updates remaining positions on the corresponding job!
    """
    valid_statuses = {"Pending", "Shortlisted", "Confirmed", "Rejected"}
    if new_status == "Accepted":
        new_status = "Confirmed"

    if new_status not in valid_statuses:
        return False, "Invalid status. Allowed: Pending, Shortlisted, Confirmed, Rejected."

    with sqlite3.connect(DATABASE_NAME) as connection:
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()

        # Verify application belongs to this employer's job
        app_row = cursor.execute(
            """
            SELECT applications.id, applications.job_id, applications.status AS current_status,
                   jobs.workers_needed, jobs.positions_remaining
            FROM applications
            JOIN jobs ON applications.job_id = jobs.id
            WHERE applications.id = ? AND jobs.employer_id = ?
            """,
            (application_id, employer_id)
        ).fetchone()

        if not app_row:
            return False, "Application not found or does not belong to your jobs."

        job_id = app_row["job_id"]

        # Check capacity if confirming
        if new_status == "Confirmed" and app_row["current_status"] != "Confirmed":
            confirmed_count = cursor.execute(
                "SELECT COUNT(*) FROM applications WHERE job_id = ? AND status IN ('Confirmed', 'Accepted')",
                (job_id,)
            ).fetchone()[0]

            if confirmed_count >= app_row["workers_needed"]:
                return False, f"Cannot confirm: All {app_row['workers_needed']} positions are already filled for this job."

        cursor.execute(
            "UPDATE applications SET status = ? WHERE id = ?",
            (new_status, application_id)
        )
        connection.commit()

        # Recalculate remaining positions for this job
        job_stats = recalculate_job_positions(job_id, connection)

        msg = f"Application status updated to '{new_status}'."
        if job_stats:
            msg += f" Remaining positions for '{job_id}': {job_stats['positions_remaining']}/{job_stats['workers_needed']}."

        return True, msg


def get_matched_workers_for_job(job_id, min_score=0):
    """
    Intelligent Worker Recommendation (Phase 06):
    Find and rank all registered workers in the database for a specific job.
    """
    job = get_job_by_id(job_id)
    if not job:
        return []

    workers = get_all_workers()
    matched_candidates = []

    for w in workers:
        match = compute_match_score(w, job)
        if match["percentage"] >= min_score:
            cand = dict(w)
            cand["match_score"] = match["score"]
            cand["match_percentage"] = match["percentage"]
            cand["match_level"] = match["level"]
            cand["match_badge_class"] = match["badge_class"]
            cand["match_breakdown"] = match["breakdown"]
            matched_candidates.append(cand)

    matched_candidates.sort(key=lambda x: x["match_score"], reverse=True)
    return matched_candidates


def insert_application(worker_id, job_id):
    """
    Worker applies for a job.
    Enforces:
    - Worker and Job exist
    - Job is Open and has remaining positions > 0
    - Worker has not already applied
    """
    with sqlite3.connect(DATABASE_NAME) as connection:
        cursor = connection.cursor()

        job = cursor.execute(
            "SELECT id, status, positions_remaining FROM jobs WHERE id = ?", (job_id,)
        ).fetchone()

        if not job:
            return None, "Job not found."

        if job[1] != "Open" or (job[2] is not None and job[2] <= 0):
            return None, "This job is already filled or closed."

        existing = cursor.execute(
            "SELECT id FROM applications WHERE worker_id = ? AND job_id = ?",
            (worker_id, job_id)
        ).fetchone()

        if existing:
            return None, "You have already applied for this job."

        cursor.execute(
            "INSERT INTO applications (worker_id, job_id, status) VALUES (?, ?, 'Pending')",
            (worker_id, job_id)
        )
        connection.commit()
        return cursor.lastrowid, "Application submitted successfully!"