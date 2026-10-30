import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash, check_password_hash

# Store the database beside this Python file
DATABASE_NAME = Path(__file__).resolve().parent / "workconnect.db"


def initialize_database():
    """
    Initialize SQLite database tables and apply schema updates if needed.
    Supports:
    - Step 1: Secure password hashing, user registration & login
    - Step 2: Role isolation, worker and employer private dashboards
    - Step 5: Trade category metadata
    - Step 7: Smart job matching with multilingual explanations
    - Step 8: Notifications, saved jobs, interviews, verification, reports
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
            password_hash TEXT,
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
            is_verified INTEGER NOT NULL DEFAULT 0,
            password_hash TEXT,
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

    # Table for saved / bookmarked jobs (Step 8)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS saved_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_id INTEGER NOT NULL,
            job_id INTEGER NOT NULL,
            saved_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (worker_id) REFERENCES workers(id),
            FOREIGN KEY (job_id) REFERENCES jobs(id),
            UNIQUE (worker_id, job_id)
        )
    """)

    # Table for real-time in-app notifications (Step 8)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_role TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            link TEXT,
            is_read INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Table for interview scheduling (Step 8)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS interviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            application_id INTEGER NOT NULL,
            employer_id INTEGER NOT NULL,
            worker_id INTEGER NOT NULL,
            interview_date TEXT NOT NULL,
            interview_time TEXT NOT NULL,
            location_or_link TEXT NOT NULL,
            notes TEXT,
            status TEXT NOT NULL DEFAULT 'Scheduled',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES jobs(id),
            FOREIGN KEY (application_id) REFERENCES applications(id),
            FOREIGN KEY (employer_id) REFERENCES employers(id),
            FOREIGN KEY (worker_id) REFERENCES workers(id)
        )
    """)

    # Table for reporting suspicious jobs or accounts (Step 8)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reporter_role TEXT NOT NULL,
            reporter_id INTEGER NOT NULL,
            target_type TEXT NOT NULL,
            target_id INTEGER NOT NULL,
            reason TEXT NOT NULL,
            details TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # -------------------------------------------------------------
    # Schema Migration / Consistency check for existing databases
    # -------------------------------------------------------------
    # 1. Ensure workers has availability, rating, password_hash
    worker_cols = [c[1] for c in cursor.execute("PRAGMA table_info(workers)").fetchall()]
    if "availability" not in worker_cols:
        cursor.execute("ALTER TABLE workers ADD COLUMN availability TEXT NOT NULL DEFAULT 'Immediate'")
    if "rating" not in worker_cols:
        cursor.execute("ALTER TABLE workers ADD COLUMN rating REAL NOT NULL DEFAULT 4.8")
    if "password_hash" not in worker_cols:
        cursor.execute("ALTER TABLE workers ADD COLUMN password_hash TEXT")

    # 2. Ensure employers has is_verified and password_hash
    employer_cols = [c[1] for c in cursor.execute("PRAGMA table_info(employers)").fetchall()]
    if "password_hash" not in employer_cols:
        cursor.execute("ALTER TABLE employers ADD COLUMN password_hash TEXT")
    if "is_verified" not in employer_cols:
        cursor.execute("ALTER TABLE employers ADD COLUMN is_verified INTEGER NOT NULL DEFAULT 0")

    # 3. Seed default password_hash for existing legacy test accounts without password
    default_hash = generate_password_hash("password123")
    cursor.execute("UPDATE workers SET password_hash = ? WHERE password_hash IS NULL OR password_hash = ''", (default_hash,))
    cursor.execute("UPDATE employers SET password_hash = ? WHERE password_hash IS NULL OR password_hash = ''", (default_hash,))

    # 4. Ensure jobs has positions_remaining
    job_cols = [c[1] for c in cursor.execute("PRAGMA table_info(jobs)").fetchall()]
    if "positions_remaining" not in job_cols:
        cursor.execute("ALTER TABLE jobs ADD COLUMN positions_remaining INTEGER NOT NULL DEFAULT 1")

    # 5. Standardize historical 'Accepted' applications to 'Confirmed'
    cursor.execute("UPDATE applications SET status = 'Confirmed' WHERE status = 'Accepted'")

    # 6. Synchronize positions_remaining for all existing jobs
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

    # 7. Ensure notifications has rich metadata columns (notification_type, job_id, company_name, job_title, location)
    notif_cols = [c[1] for c in cursor.execute("PRAGMA table_info(notifications)").fetchall()]
    if "notification_type" not in notif_cols:
        cursor.execute("ALTER TABLE notifications ADD COLUMN notification_type TEXT DEFAULT 'JOB_POSTED'")
    if "job_id" not in notif_cols:
        cursor.execute("ALTER TABLE notifications ADD COLUMN job_id INTEGER")
    if "company_name" not in notif_cols:
        cursor.execute("ALTER TABLE notifications ADD COLUMN company_name TEXT")
    if "job_title" not in notif_cols:
        cursor.execute("ALTER TABLE notifications ADD COLUMN job_title TEXT")
    if "location" not in notif_cols:
        cursor.execute("ALTER TABLE notifications ADD COLUMN location TEXT")

    connection.commit()
    connection.close()

    print("WorkConnect database initialized and synchronized successfully!")


def compute_match_score(worker, job, lang="en"):
    """
    Intelligent Matching Engine (Step 7):
    Calculates a 0-100 match score based on 6 key dimensions:
    1. Skill match (up to 35 pts) - required skill vs worker skill
    2. Location match (up to 20 pts) - proximity and locality match
    3. Experience match (up to 15 pts) - years of experience
    4. Wage compatibility (up to 15 pts) - worker expected wage vs job daily wage
    5. Availability match (up to 10 pts) - worker readiness
    6. Rating score (up to 5 pts) - worker track record & feedback

    Also provides multilingual explanations in English (en), Telugu (te), and Hindi (hi).
    """
    w = dict(worker) if hasattr(worker, "keys") else worker
    j = dict(job) if hasattr(job, "keys") else job
    lang = lang if lang in ("en", "te", "hi") else "en"

    reasons = []

    # 1. Skill Match (Max: 35 pts)
    w_skill = (w.get("skill") or "").strip().lower()
    j_skill = (j.get("skill_required") or "").strip().lower()
    j_title = (j.get("title") or "").strip().lower()
    j_desc = (j.get("description") or "").strip().lower()

    if w_skill and j_skill:
        if w_skill == j_skill:
            skill_score = 35.0
            skill_desc = "Exact skill match"
            if lang == "te":
                reasons.append(f"✓ మీ వృత్తికి సరిగ్గా సరిపోతుంది ({w.get('skill')})")
            elif lang == "hi":
                reasons.append(f"✓ आपके हुनर से बिल्कुल मेल खाता है ({w.get('skill')})")
            else:
                reasons.append(f"✓ Exact skill match ({w.get('skill')})")
        elif w_skill in j_skill or j_skill in w_skill:
            skill_score = 25.0
            skill_desc = "Strong skill overlap"
            if lang == "te":
                reasons.append("✓ సంబంధిత వృత్తి నైపుణ్యం ఉంది")
            elif lang == "hi":
                reasons.append("✓ कार्य से संबंधित मजबूत हुनर")
            else:
                reasons.append("✓ Strong trade skill relevance")
        elif w_skill in j_title or w_skill in j_desc:
            skill_score = 18.0
            skill_desc = "Skill mentioned in job description"
            if lang == "te":
                reasons.append("✓ పని వివరాలలో మీ నైపుణ్యం అవసరం ఉంది")
            elif lang == "hi":
                reasons.append("✓ काम के विवरण में आपके हुनर की मांग")
            else:
                reasons.append("✓ Skill aligns with job requirements")
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
            if lang == "te":
                reasons.append(f"✓ మీ సొంత ఊరు లేదా ప్రాంతంలోనే పని ({w.get('location')})")
            elif lang == "hi":
                reasons.append(f"✓ आपके अपने स्थान पर ही काम उपलब्ध ({w.get('location')})")
            else:
                reasons.append(f"✓ Same locality ({w.get('location')})")
        elif w_loc in j_loc or j_loc in w_loc:
            loc_score = 12.0
            loc_desc = "Same region / neighboring area"
            if lang == "te":
                reasons.append("✓ దగ్గర ప్రాంతంలో అందుబాటులో ఉన్న పని")
            elif lang == "hi":
                reasons.append("✓ नजदीकी क्षेत्र में काम उपलब्ध")
            else:
                reasons.append("✓ Neighboring region")
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
        if lang == "te":
            reasons.append(f"✓ {exp} ఏళ్ల నిపుణత అనుభవం")
        elif lang == "hi":
            reasons.append(f"✓ {exp} वर्षों का विशेषज्ञ अनुभव")
        else:
            reasons.append(f"✓ Expert track record ({exp} yrs)")
    elif exp >= 3:
        exp_score = 13.0
        exp_desc = f"Experienced ({exp} yrs exp)"
        if lang == "te":
            reasons.append(f"✓ {exp} ఏళ్ల చక్కని అనుభవం")
        elif lang == "hi":
            reasons.append(f"✓ {exp} वर्षों का अच्छा अनुभव")
        else:
            reasons.append(f"✓ Experienced worker ({exp} yrs)")
    elif exp >= 1:
        exp_score = 10.0
        exp_desc = f"Competent ({exp} yrs exp)"
        if lang == "te":
            reasons.append(f"✓ {exp} సంవత్సరం పని అనుభవం")
        elif lang == "hi":
            reasons.append(f"✓ {exp} वर्ष का व्यावहारिक अनुभव")
        else:
            reasons.append(f"✓ Competent ({exp} yr exp)")
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
            if lang == "te":
                reasons.append(f"✓ ఆశించిన కూలీ (₹{w_wage}) కన్నా ఎక్కువ లేదా సమానం (₹{j_wage})")
            elif lang == "hi":
                reasons.append(f"✓ अपेक्षित मजदूरी (₹{w_wage}) से बराबर या बेहतर (₹{j_wage})")
            else:
                reasons.append(f"✓ Offered wage meets or exceeds expected (₹{w_wage} ≤ ₹{j_wage})")
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
        if lang == "te":
            reasons.append("✓ వెంటనే చేరడానికి సిద్ధంగా ఉన్నారు")
        elif lang == "hi":
            reasons.append("✓ तुरंत काम शुरू करने के लिए उपलब्ध")
        else:
            reasons.append("✓ Ready to join immediately")
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
        "reasons": reasons,
        "explanation": " • ".join(reasons) if reasons else "Profile reviewed for compatibility.",
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


def get_employer_by_id(employer_id):
    """Return an employer by ID (or None)."""
    with sqlite3.connect(DATABASE_NAME) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            "SELECT * FROM employers WHERE id = ?", (employer_id,)
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

        # Step 8: Trigger in-app notification for worker
        try:
            worker_info = cursor.execute("SELECT worker_id, job_id FROM applications WHERE id = ?", (application_id,)).fetchone()
            if worker_info:
                w_id, j_id = worker_info[0], worker_info[1]
                j_row = cursor.execute("SELECT title FROM jobs WHERE id = ?", (j_id,)).fetchone()
                j_title = j_row[0] if j_row else "Job"
                cursor.execute(
                    """
                    INSERT INTO notifications (user_role, user_id, title, message, link)
                    VALUES ('worker', ?, ?, ?, ?)
                    """,
                    (w_id, f"Application {new_status}", f"Your application for '{j_title}' has been updated to '{new_status}'.", "/worker/dashboard")
                )
                connection.commit()
        except Exception:
            pass

        # Recalculate remaining positions for this job
        job_stats = recalculate_job_positions(job_id, connection)

        msg = f"Application status updated to '{new_status}'."
        if job_stats:
            msg += f" Remaining positions for job #{job_id}: {job_stats['positions_remaining']}/{job_stats['workers_needed']}."

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
            cand["match_reasons"] = match.get("reasons", [])
            cand["match_explanation"] = match.get("explanation", "")
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


# =====================================================================
# STEP 1 & 2: USER AUTHENTICATION, PASSWORD HASHING, & PROFILE HELPERS
# =====================================================================

def create_worker(name, email, password, skill, location, experience=0, wage=0, availability="Immediate", rating=4.8):
    """Create a new worker account with securely hashed password."""
    password_hash = generate_password_hash(password)
    with sqlite3.connect(DATABASE_NAME) as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO workers
            (name, email, password_hash, skill, location, experience, wage, availability, rating)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (name.strip(), email.strip().lower(), password_hash, skill.strip(), location.strip(), experience, wage, availability.strip(), rating)
        )
        connection.commit()
        return cursor.lastrowid


def create_employer(name, email, password, employer_type, location, is_verified=0):
    """Create a new employer account with securely hashed password."""
    password_hash = generate_password_hash(password)
    with sqlite3.connect(DATABASE_NAME) as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO employers
            (name, email, password_hash, employer_type, location, is_verified)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (name.strip(), email.strip().lower(), password_hash, employer_type.strip(), location.strip(), is_verified)
        )
        connection.commit()
        return cursor.lastrowid


def verify_worker_credentials(email, password):
    """Verify worker credentials using secure password hashing."""
    worker = get_worker_by_email(email)
    if not worker:
        return None
    stored_hash = worker.get("password_hash")
    if stored_hash and check_password_hash(stored_hash, password):
        return worker
    # Default demo password for seed data
    if not stored_hash and password == "password123":
        return worker
    return None


def verify_employer_credentials(email, password):
    """Verify employer credentials using secure password hashing."""
    employer = get_employer_by_email(email)
    if not employer:
        return None
    stored_hash = employer.get("password_hash")
    if stored_hash and check_password_hash(stored_hash, password):
        return employer
    # Default demo password for seed data
    if not stored_hash and password == "password123":
        return employer
    return None


def update_worker_profile(worker_id, name, skill, location, experience, wage, availability):
    """Allow workers to correct and update their profile and preferences (Step 7)."""
    with sqlite3.connect(DATABASE_NAME) as connection:
        connection.execute(
            """
            UPDATE workers
            SET name = ?, skill = ?, location = ?, experience = ?, wage = ?, availability = ?
            WHERE id = ?
            """,
            (name.strip(), skill.strip(), location.strip(), experience, wage, availability.strip(), worker_id)
        )
        connection.commit()
        return True


def update_employer_profile(employer_id, name, employer_type, location, is_verified=None):
    """Update employer profile."""
    with sqlite3.connect(DATABASE_NAME) as connection:
        if is_verified is not None:
            connection.execute(
                """
                UPDATE employers
                SET name = ?, employer_type = ?, location = ?, is_verified = ?
                WHERE id = ?
                """,
                (name.strip(), employer_type.strip(), location.strip(), 1 if is_verified else 0, employer_id)
            )
        else:
            connection.execute(
                """
                UPDATE employers
                SET name = ?, employer_type = ?, location = ?
                WHERE id = ?
                """,
                (name.strip(), employer_type.strip(), location.strip(), employer_id)
            )
        connection.commit()
        return True


def toggle_employer_verification(employer_id, is_verified=None):
    """Toggle or set employer verification status (Step 8)."""
    with sqlite3.connect(DATABASE_NAME) as connection:
        if is_verified is None:
            connection.execute(
                "UPDATE employers SET is_verified = CASE WHEN is_verified = 1 THEN 0 ELSE 1 END WHERE id = ?",
                (employer_id,)
            )
        else:
            connection.execute(
                "UPDATE employers SET is_verified = ? WHERE id = ?",
                (1 if is_verified else 0, employer_id)
            )
        connection.commit()
        return True


# =====================================================================
# STEP 8: SAVED JOBS, NOTIFICATIONS, INTERVIEWS, AND REPORTS HELPERS
# =====================================================================

def save_job_for_worker(worker_id, job_id):
    """Bookmark a job for a worker."""
    with sqlite3.connect(DATABASE_NAME) as connection:
        try:
            connection.execute(
                "INSERT INTO saved_jobs (worker_id, job_id) VALUES (?, ?)",
                (worker_id, job_id)
            )
            connection.commit()
            return True, "Job saved to your bookmarks."
        except sqlite3.IntegrityError:
            return False, "Job is already saved in your bookmarks."


def unsave_job_for_worker(worker_id, job_id):
    """Remove a bookmarked job."""
    with sqlite3.connect(DATABASE_NAME) as connection:
        connection.execute(
            "DELETE FROM saved_jobs WHERE worker_id = ? AND job_id = ?",
            (worker_id, job_id)
        )
        connection.commit()
        return True, "Job removed from saved list."


def is_job_saved_by_worker(worker_id, job_id):
    """Check if a job is saved by worker."""
    if not worker_id:
        return False
    with sqlite3.connect(DATABASE_NAME) as connection:
        row = connection.execute(
            "SELECT id FROM saved_jobs WHERE worker_id = ? AND job_id = ?",
            (worker_id, job_id)
        ).fetchone()
        return bool(row)


def get_saved_jobs_by_worker(worker_id):
    """Retrieve all saved jobs with employer info."""
    with sqlite3.connect(DATABASE_NAME) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT jobs.*, employers.name AS employer_name, employers.is_verified AS employer_is_verified, saved_jobs.saved_at
            FROM saved_jobs
            JOIN jobs ON saved_jobs.job_id = jobs.id
            JOIN employers ON jobs.employer_id = employers.id
            WHERE saved_jobs.worker_id = ?
            ORDER BY saved_jobs.id DESC
            """,
            (worker_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def create_notification(user_role, user_id, title, message, link=None,
                        notification_type="JOB_POSTED", job_id=None,
                        company_name=None, job_title=None, location=None):
    """Create in-app notification with support for rich metadata."""
    with sqlite3.connect(DATABASE_NAME) as connection:
        connection.execute(
            """
            INSERT INTO notifications (user_role, user_id, title, message, link,
                                       notification_type, job_id, company_name, job_title, location)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_role, user_id, title, message, link,
             notification_type, job_id, company_name, job_title, location)
        )
        connection.commit()
        return True


def get_notifications(user_role, user_id, unread_only=False):
    """Get notifications for a user in reverse chronological order with formatted metadata."""
    from datetime import datetime, timezone

    def _relative_time(ts_str):
        if not ts_str:
            return "Recently"
        formats = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d"]
        dt = None
        for fmt in formats:
            try:
                dt = datetime.strptime(str(ts_str).strip(), fmt)
                break
            except Exception:
                continue
        if not dt:
            return str(ts_str)
        now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
        diff = int((now_utc - dt).total_seconds())
        if diff < 45:
            return "Just now"
        if diff < 3600:
            return f"{max(1, diff // 60)}m ago"
        if diff < 86400:
            return f"{diff // 3600}h ago"
        if diff < 604800:
            return f"{diff // 86400}d ago"
        return dt.strftime("%b %d, %Y")

    with sqlite3.connect(DATABASE_NAME) as connection:
        connection.row_factory = sqlite3.Row
        query = "SELECT * FROM notifications WHERE user_role = ? AND user_id = ?"
        params = [user_role, user_id]
        if unread_only:
            query += " AND is_read = 0"
        query += " ORDER BY id DESC LIMIT 50"
        rows = connection.execute(query, params).fetchall()
        
        result = []
        for r in rows:
            item = dict(r)
            item["time_display"] = _relative_time(item.get("created_at"))
            # Fallback metadata if not set
            if not item.get("job_title") and item.get("title"):
                item["job_title"] = item.get("title")
            if not item.get("company_name"):
                item["company_name"] = "WorkConnect"
            if not item.get("location"):
                item["location"] = "Local"
            if not item.get("link"):
                if item.get("job_id"):
                    item["link"] = f"/jobs/{item['job_id']}"
                else:
                    item["link"] = "/worker/dashboard" if user_role == "worker" else "/employer/dashboard"
            result.append(item)
        return result


def get_unread_notifications_count(user_role, user_id):
    """Count unread notifications."""
    if not user_id:
        return 0
    with sqlite3.connect(DATABASE_NAME) as connection:
        row = connection.execute(
            "SELECT COUNT(*) FROM notifications WHERE user_role = ? AND user_id = ? AND is_read = 0",
            (user_role, user_id)
        ).fetchone()
        return row[0] if row else 0


def mark_notification_as_read(notification_id, user_role, user_id):
    """Mark a specific notification as read."""
    with sqlite3.connect(DATABASE_NAME) as connection:
        connection.execute(
            "UPDATE notifications SET is_read = 1 WHERE id = ? AND user_role = ? AND user_id = ?",
            (notification_id, user_role, user_id)
        )
        connection.commit()
        return True


def mark_all_notifications_as_read(user_role, user_id):
    """Mark all user notifications as read."""
    with sqlite3.connect(DATABASE_NAME) as connection:
        connection.execute(
            "UPDATE notifications SET is_read = 1 WHERE user_role = ? AND user_id = ?",
            (user_role, user_id)
        )
        connection.commit()
        return True


def schedule_interview(job_id, application_id, employer_id, worker_id, interview_date, interview_time, location_or_link, notes=""):
    """Schedule an interview between employer and worker (Step 8)."""
    with sqlite3.connect(DATABASE_NAME) as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO interviews
            (job_id, application_id, employer_id, worker_id, interview_date, interview_time, location_or_link, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (job_id, application_id, employer_id, worker_id, interview_date, interview_time, location_or_link, notes)
        )
        connection.commit()
        interview_id = cursor.lastrowid

        # Trigger notification for the worker
        job = get_job_by_id(job_id)
        job_title = job["title"] if job else "Job"
        notif_msg = f"Interview scheduled for '{job_title}' on {interview_date} at {interview_time}."
        cursor.execute(
            "INSERT INTO notifications (user_role, user_id, title, message, link) VALUES ('worker', ?, ?, ?, ?)",
            (worker_id, "Interview Scheduled", notif_msg, "/worker/dashboard")
        )
        connection.commit()
        return interview_id


def get_interviews_for_worker(worker_id):
    """Retrieve interviews for a worker."""
    with sqlite3.connect(DATABASE_NAME) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT interviews.*, jobs.title AS job_title, employers.name AS employer_name, employers.location AS employer_location
            FROM interviews
            JOIN jobs ON interviews.job_id = jobs.id
            JOIN employers ON interviews.employer_id = employers.id
            WHERE interviews.worker_id = ?
            ORDER BY interviews.interview_date ASC, interviews.interview_time ASC
            """,
            (worker_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def get_interviews_for_employer(employer_id, job_id=None):
    """Retrieve interviews scheduled by an employer."""
    with sqlite3.connect(DATABASE_NAME) as connection:
        connection.row_factory = sqlite3.Row
        query = """
            SELECT interviews.*, jobs.title AS job_title, workers.name AS worker_name, workers.email AS worker_email, workers.skill AS worker_skill
            FROM interviews
            JOIN jobs ON interviews.job_id = jobs.id
            JOIN workers ON interviews.worker_id = workers.id
            WHERE interviews.employer_id = ?
        """
        params = [employer_id]
        if job_id:
            query += " AND interviews.job_id = ?"
            params.append(job_id)
        query += " ORDER BY interviews.interview_date ASC, interviews.interview_time ASC"
        rows = connection.execute(query, params).fetchall()
        return [dict(r) for r in rows]


def submit_report(reporter_role, reporter_id, target_type, target_id, reason, details=""):
    """Submit a report for suspicious job, worker, or employer (Step 8)."""
    with sqlite3.connect(DATABASE_NAME) as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO reports (reporter_role, reporter_id, target_type, target_id, reason, details)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (reporter_role, reporter_id, target_type, target_id, reason, details)
        )
        connection.commit()
        return cursor.lastrowid


def get_all_reports():
    """Retrieve all reports for moderation."""
    with sqlite3.connect(DATABASE_NAME) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute("SELECT * FROM reports ORDER BY id DESC").fetchall()
        return [dict(r) for r in rows]