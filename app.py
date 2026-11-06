import os
import sqlite3
from datetime import timedelta
from functools import wraps
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    jsonify,
    make_response,
    abort
)
from werkzeug.security import generate_password_hash

from database import (
    DATABASE_NAME,
    initialize_database,
    compute_match_score,
    get_all_jobs,
    get_job_by_id,
    get_worker_by_email,
    get_worker_by_id,
    get_all_workers,
    get_employer_by_email,
    get_employer_by_id,
    get_applications_by_employer,
    get_applications_by_worker,
    update_application_status,
    get_matched_workers_for_job,
    recalculate_job_positions,
    insert_application,
    create_worker,
    create_employer,
    verify_worker_credentials,
    verify_employer_credentials,
    reset_worker_password,
    reset_employer_password,
    update_worker_profile,
    update_employer_profile,
    toggle_employer_verification,
    save_job_for_worker,
    unsave_job_for_worker,
    is_job_saved_by_worker,
    get_saved_jobs_by_worker,
    create_notification,
    get_notifications,
    mark_notification_as_read,
    mark_all_notifications_as_read,
    get_unread_notifications_count,
    schedule_interview,
    get_interviews_for_worker,
    get_interviews_for_employer,
    submit_report,
    get_all_reports
)

from translations import get_translation, SUPPORTED_LANGUAGES
from trade_utils import get_trade_for_skill, get_all_trades_list, TRADE_METADATA
from ai_services import ask_workconnect_assistant, extract_registration_fields_from_transcript
from notification_service import notify_workers_new_job, format_relative_time

app = Flask(__name__)

# Step 1: Session Security Configuration & Permanent Sessions
app.secret_key = os.environ.get("SECRET_KEY", "workconnect-super-secure-session-key-2026")
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=30)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# Initialize database schema and migrate existing data
initialize_database()


# =====================================================================
# STEP 3: CONTEXT PROCESSOR & LANGUAGE SWITCHING
# =====================================================================

@app.before_request
def setup_user_language():
    """Ensure session language is set and synchronized with cookie."""
    if "lang" not in session:
        cookie_lang = request.cookies.get("workconnect_lang")
        if cookie_lang in SUPPORTED_LANGUAGES:
            session["lang"] = cookie_lang
        else:
            session["lang"] = "en"


@app.context_processor
def inject_global_template_vars():
    """Inject current user, roles, language, unread notifications, and translations into all templates."""
    lang = session.get("lang", "en")
    if lang not in SUPPORTED_LANGUAGES:
        lang = "en"

    user_id = session.get("user_id")
    role = session.get("role")
    current_user = None
    unread_count = 0

    if user_id and role == "worker":
        current_user = get_worker_by_id(user_id)
        unread_count = get_unread_notifications_count("worker", user_id)
    elif user_id and role == "employer":
        with sqlite3.connect(DATABASE_NAME) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM employers WHERE id = ?", (user_id,)).fetchone()
            current_user = dict(row) if row else None
        unread_count = get_unread_notifications_count("employer", user_id)

    def translate_helper(key, default=None):
        return get_translation(key, lang=lang, default=default)

    return {
        "current_user": current_user,
        "user_role": role,
        "active_lang": lang,
        "unread_notifications_count": unread_count,
        "t": translate_helper,
        "available_trades": get_all_trades_list(lang=lang)
    }


@app.route("/set-language/<lang_code>")
def set_language(lang_code):
    """Switch language between English ('en'), Telugu ('te'), and Hindi ('hi')."""
    if lang_code in SUPPORTED_LANGUAGES:
        session["lang"] = lang_code

    next_url = request.referrer or url_for("home")
    # Avoid redirect loop to set-language
    if "/set-language/" in next_url:
        next_url = url_for("home")

    response = make_response(redirect(next_url))
    if lang_code in SUPPORTED_LANGUAGES:
        response.set_cookie("workconnect_lang", lang_code, max_age=30 * 24 * 3600)
    return response


# =====================================================================
# STEP 1 & 2: AUTHENTICATION, AUTHORIZATION DECORATORS, & ROLES
# =====================================================================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please sign in to access this page.", "warning")
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def worker_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please sign in as a worker to proceed.", "warning")
            return redirect(url_for("login", role="worker", next=request.url))
        if session.get("role") != "worker":
            flash("Unauthorized. This area is reserved for workers.", "danger")
            return redirect(url_for("home"))
        return f(*args, **kwargs)
    return decorated_function


def employer_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please sign in as an employer to access this portal.", "warning")
            return redirect(url_for("login", role="employer", next=request.url))
        if session.get("role") != "employer":
            flash("Unauthorized. This area is reserved for employers.", "danger")
            return redirect(url_for("home"))
        return f(*args, **kwargs)
    return decorated_function


@app.route("/login", methods=["GET", "POST"])
def login():
    """Unified login for workers and employers with secure password hashing & permanent session."""
    active_tab = request.args.get("role", "worker").strip().lower()
    next_url = request.args.get("next", "")

    if request.method == "POST":
        role = request.form.get("role", "worker").strip().lower()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()
        next_url = request.form.get("next", "").strip()

        if not email or not password:
            return render_template(
                "login.html",
                error="Please enter both email and password.",
                active_tab=role,
                next_url=next_url
            )

        if role == "employer":
            employer = verify_employer_credentials(email, password)
            if employer:
                session.clear()
                session.permanent = True
                session["user_id"] = employer["id"]
                session["role"] = "employer"
                session["email"] = employer["email"]
                session["name"] = employer["name"]
                flash(f"Welcome back, {employer['name']}!", "success")
                if next_url and next_url.startswith("/") and not next_url.startswith("/worker"):
                    return redirect(next_url)
                return redirect(url_for("employer_dashboard"))
            else:
                return render_template(
                    "login.html",
                    error="Invalid employer email or password.",
                    active_tab="employer",
                    next_url=next_url
                )
        else:
            worker = verify_worker_credentials(email, password)
            if worker:
                session.clear()
                session.permanent = True
                session["user_id"] = worker["id"]
                session["role"] = "worker"
                session["email"] = worker["email"]
                session["name"] = worker["name"]
                flash(f"Welcome back, {worker['name']}!", "success")
                if next_url and next_url.startswith("/") and not next_url.startswith("/employer"):
                    return redirect(next_url)
                return redirect(url_for("worker_dashboard"))
            else:
                return render_template(
                    "login.html",
                    error="Invalid worker email or password.",
                    active_tab="worker",
                    next_url=next_url
                )

    return render_template("login.html", active_tab=active_tab, next_url=next_url)


@app.route("/logout")
def logout():
    """Secure logout clearing user session."""
    user_name = session.get("name", "User")
    session.clear()
    flash(f"Goodbye {user_name}, you have been safely logged out.", "info")
    return redirect(url_for("home"))


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    """Allow an account owner to reset their password using their registered email."""
    active_tab = request.args.get("role", "worker").strip().lower()

    if request.method == "POST":
        role = request.form.get("role", "worker").strip().lower()
        email = request.form.get("email", "").strip().lower()
        new_password = request.form.get("new_password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()

        if not email or not new_password or not confirm_password:
            return render_template(
                "forgot_password.html",
                error="Please complete all fields.",
                active_tab=role,
                email=email
            )
        if len(new_password) < 8:
            return render_template(
                "forgot_password.html",
                error="New password must be at least 8 characters.",
                active_tab=role,
                email=email
            )
        if new_password != confirm_password:
            return render_template(
                "forgot_password.html",
                error="Passwords do not match.",
                active_tab=role,
                email=email
            )

        if role == "employer":
            reset = reset_employer_password(email, new_password)
        else:
            reset = reset_worker_password(email, new_password)

        if not reset:
            return render_template(
                "forgot_password.html",
                error="No account was found for this email in the selected role.",
                active_tab=role,
                email=email
            )

        flash("Your password has been reset. You can now log in.", "success")
        return redirect(url_for("login", role=role))

    return render_template("forgot_password.html", active_tab=active_tab)


# =====================================================================
# STEP 1, 2, & 4: REGISTRATION ROUTES (WORKER, EMPLOYER, VOICE AI)
# =====================================================================

@app.route("/")
def home():
    """WorkConnect Homepage."""
    return render_template("index.html")


@app.route("/register/worker", methods=["GET", "POST"])
def worker_register():
    """Worker Registration with secure password hashing (Step 1)."""
    if session.get("role") == "employer":
        flash("Unauthorized. You are currently signed in as an employer. Please log out to register as a worker.", "danger")
        return redirect(url_for("home"))
    if session.get("role") == "worker":
        return redirect(url_for("worker_dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()
        skill = request.form.get("skill", "").strip()
        location = request.form.get("location", "").strip()
        availability = request.form.get("availability", "Immediate").strip()

        try:
            experience = int(request.form.get("experience", "0"))
            wage = int(request.form.get("wage", "0"))
        except ValueError:
            return "Experience and wage must be valid numbers.", 400

        rating = None
        if request.form.get("rating"):
            try:
                rating = float(request.form.get("rating"))
                rating = min(5.0, max(1.0, rating))
            except ValueError:
                return "Rating must be a valid number.", 400

        if not all([name, email, skill, location]):
            return "Please complete all required fields.", 400

        if password and confirm_password and password != confirm_password:
            return "Passwords do not match. Please try again.", 400

        if not password:
            password = "password123"

        if experience < 0 or experience > 60 or wage < 0:
            return "Please enter a valid experience and wage.", 400

        try:
            worker_id = create_worker(
                name=name,
                email=email,
                password=password,
                skill=skill,
                location=location,
                experience=experience,
                wage=wage,
                availability=availability,
                rating=rating
            )

            # Auto-login newly registered worker with permanent session
            session.permanent = True
            session["user_id"] = worker_id
            session["role"] = "worker"
            session["email"] = email
            session["name"] = name

            create_notification(
                user_role="worker",
                user_id=worker_id,
                title="Welcome to WorkConnect!",
                message=f"Welcome {name}! Your worker profile is now active. Browse jobs and start applying.",
                link="/jobs"
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


@app.route("/register/worker/voice")
def worker_voice_register():
    """Interactive Voice AI Registration Wizard (Step 4)."""
    if session.get("role") == "employer":
        flash("Unauthorized. This area is reserved for workers.", "danger")
        return redirect(url_for("home"))
    return render_template("voice_register.html")


@app.route("/register/employer", methods=["GET", "POST"])
def employer_register():
    """Employer Registration with secure password hashing (Step 1)."""
    if session.get("role") == "worker":
        flash("Unauthorized. You are currently signed in as a worker. Please log out to register as an employer.", "danger")
        return redirect(url_for("home"))
    if session.get("role") == "employer":
        return redirect(url_for("employer_dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()
        employer_type = request.form.get("type", "").strip()
        location = request.form.get("location", "").strip()

        if not all([name, email, employer_type, location]):
            return "Please complete all required fields.", 400

        if password and confirm_password and password != confirm_password:
            return "Passwords do not match. Please try again.", 400

        if not password:
            password = "password123"

        try:
            employer_id = create_employer(
                name=name,
                email=email,
                password=password,
                employer_type=employer_type,
                location=location
            )

            # Auto-login newly registered employer with permanent session
            session.permanent = True
            session["user_id"] = employer_id
            session["role"] = "employer"
            session["email"] = email
            session["name"] = name

            create_notification(
                user_role="employer",
                user_id=employer_id,
                title="Welcome to WorkConnect!",
                message=f"Welcome {name}! You can now post job requirements and discover matched talent.",
                link="/jobs/post"
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


# =====================================================================
# STEP 2, 5, & 7: BROWSE JOBS, VISUAL TRADES, & JOB POSTING
# =====================================================================

@app.route("/jobs")
def browse_jobs():
    """
    Search and browse jobs (Steps 5 & 7):
    - Visual Trade recognition (Mason, Driver, Electrician, Painter, Farm-worker)
    - Audio playback for job descriptions
    - High-visibility daily wage badges and locality
    - Personalized intelligent match scoring
    - Saved job indicator
    """
    search_query = request.args.get("q", "").strip()
    skill_filter = request.args.get("skill", "").strip()
    location_filter = request.args.get("location", "").strip()
    max_wage = request.args.get("max_wage", "").strip()
    worker_email = request.args.get("worker_email", "").strip().lower()

    # If logged in as worker, prioritize logged-in worker email
    if session.get("role") == "worker" and session.get("email"):
        worker_email = session["email"]

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

    # Attach visual trade metadata and saved job state for worker
    current_worker_id = session.get("user_id") if session.get("role") == "worker" else None
    for j in jobs:
        trade_meta = get_trade_for_skill(j["skill_required"])
        j["trade_image"] = trade_meta["image"]
        j["trade_icon"] = trade_meta["icon"]
        j["trade_color"] = trade_meta["color"]
        j["trade_bg_tint"] = trade_meta["bg_tint"]
        j["is_saved"] = is_job_saved_by_worker(current_worker_id, j["id"]) if current_worker_id else False

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


@app.route("/jobs/post", methods=["GET", "POST"])
@employer_required
def post_job():
    """
    Post a Job Requirement (Protected: Employer only).
    Automatically attaches to authenticated employer session.
    """
    employer = None
    if session.get("user_id"):
        employer = get_employer_by_id(session["user_id"])
    if not employer and session.get("email"):
        employer = get_employer_by_email(session["email"])

    if not employer:
        flash("Employer profile not found. Please log in again.", "danger")
        return redirect(url_for("login", role="employer"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        skill = request.form.get("skill_required", "").strip()
        description = request.form.get("description", "").strip()
        location = request.form.get("location", "").strip()

        try:
            workers_needed = int(request.form.get("workers_needed", "0"))
            daily_wage = int(request.form.get("daily_wage", "-1"))
        except ValueError:
            return "Workers needed and daily wage must be valid whole numbers.", 400

        if not all([title, skill, description, location]):
            return "Please complete all required fields.", 400

        if not (1 <= workers_needed <= 10000) or daily_wage < 0:
            return "Please enter a valid number of workers and wage.", 400

        try:
            with sqlite3.connect(DATABASE_NAME) as connection:
                connection.execute("PRAGMA foreign_keys = ON")
                cursor = connection.cursor()
                cursor.execute(
                    """
                    INSERT INTO jobs
                    (employer_id, title, skill_required, description,
                     location, workers_needed, positions_remaining, daily_wage, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Open')
                    """,
                    (
                        employer["id"], title, skill, description,
                        location, workers_needed, workers_needed, daily_wage
                    )
                )
                connection.commit()
                new_job_id = cursor.lastrowid

            # Trigger in-app notifications for registered workers (Job Posting Notification System)
            try:
                notify_workers_new_job(new_job_id)
            except Exception as notif_err:
                app.logger.warning(f"Could not trigger worker notifications for job #{new_job_id}: {notif_err}")

            flash(f"Job '{title}' posted successfully with {workers_needed} positions open!", "success")
            return redirect(url_for("employer_dashboard"))

        except sqlite3.IntegrityError:
            return "Could not save the job. Please check the submitted details.", 400

    return render_template("job_post.html", employer=employer)


@app.route("/jobs/<int:job_id>")
def job_details(job_id):
    """
    Dedicated Job Details Page:
    Displays complete specifications, trade imagery, live remaining positions,
    personalized match compatibility breakdown for workers, and audio voiceover.
    Automatically marks notification as read if accessed via a notification link.
    """
    job = get_job_by_id(job_id)
    if job is None:
        flash("The requested job posting was not found.", "warning")
        return redirect(url_for("browse_jobs"))

    # If opened from notification, mark that notification read
    notif_id = request.args.get("notif_id")
    if notif_id and session.get("user_id") and session.get("role") == "worker":
        try:
            mark_notification_as_read(int(notif_id), "worker", session["user_id"])
        except Exception:
            pass

    # Visual trade assets and time formatting
    trade_meta = get_trade_for_skill(job["skill_required"])
    job["trade_image"] = trade_meta["image"]
    job["trade_icon"] = trade_meta["icon"]
    job["trade_color"] = trade_meta["color"]
    job["posted_time_display"] = format_relative_time(job.get("created_at"))

    match_info = None
    has_applied = False
    application_status = None
    is_saved = False

    if session.get("user_id") and session.get("role") == "worker":
        worker = get_worker_by_id(session["user_id"])
        if worker:
            match_info = compute_match_score(worker, job, lang=session.get("lang", "en"))
            is_saved = is_job_saved_by_worker(worker["id"], job_id)
            with sqlite3.connect(DATABASE_NAME) as conn:
                app_row = conn.execute(
                    "SELECT status FROM applications WHERE worker_id = ? AND job_id = ?",
                    (worker["id"], job_id)
                ).fetchone()
                if app_row:
                    has_applied = True
                    application_status = app_row[0]

    return render_template(
        "job_details.html",
        job=job,
        match_info=match_info,
        has_applied=has_applied,
        application_status=application_status,
        is_saved=is_saved
    )


@app.route("/jobs/<int:job_id>/apply", methods=["GET", "POST"])
@worker_required
def apply_job(job_id):
    """
    Apply for Job (Protected: Worker only).
    Enforces authorization: workers apply using their own verified account.
    """
    job = get_job_by_id(job_id)
    if job is None:
        return "Job not found.", 404

    # Calculate live remaining positions
    job_stats = recalculate_job_positions(job_id)
    if job_stats and job_stats["positions_remaining"] <= 0:
        return "This job has already been filled. No open positions remain.", 400

    worker = get_worker_by_id(session["user_id"])
    if not worker:
        flash("Worker account not found.", "danger")
        return redirect(url_for("login", role="worker"))

    match_info = compute_match_score(worker, job, lang=session.get("lang", "en"))

    if request.method == "POST":
        # Enforce that workers only apply as themselves
        worker_id = worker["id"]

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
                    (worker_id, job["id"])
                )

            # Trigger notification for the employer (Step 8)
            create_notification(
                user_role="employer",
                user_id=job["employer_id"],
                title="New Job Applicant!",
                message=f"{worker['name']} ({worker['skill']}) just applied for '{job['title']}'.",
                link="/employer/dashboard"
            )

            flash(f"Application for '{job['title']}' submitted successfully! You can track it here.", "success")
            return redirect(url_for("worker_dashboard"))

        except sqlite3.IntegrityError:
            return """
                <h2>Application Already Submitted</h2>
                <p>You have already applied for this job opportunity.</p>
                <a href="/jobs">Return to Browse Jobs</a>
            """, 400

    # Attach visual trade metadata
    trade_meta = get_trade_for_skill(job["skill_required"])
    job["trade_image"] = trade_meta["image"]
    job["trade_icon"] = trade_meta["icon"]
    job["trade_color"] = trade_meta["color"]

    return render_template(
        "apply_job.html",
        job=job,
        worker=worker,
        worker_email=worker["email"],
        match_info=match_info
    )


# =====================================================================
# STEP 2 & 8: PRIVATE DASHBOARDS & DATA ISOLATION CONTROLS
# =====================================================================

@app.route("/worker/dashboard")
@worker_required
def worker_dashboard():
    """
    Private Worker Dashboard (Step 2):
    Displays worker's personal profile, live applications, saved jobs, notifications, and scheduled interviews.
    Strict privacy isolation: workers can ONLY view their own data.
    """
    worker = get_worker_by_id(session["user_id"])
    if not worker:
        flash("Worker session invalid. Please log in.", "danger")
        return redirect(url_for("login", role="worker"))

    sort_by = request.args.get("sort_by", "date").strip()
    applications = get_applications_by_worker(worker["email"], sort_by=sort_by)
    saved_jobs = get_saved_jobs_by_worker(worker["id"])
    interviews = get_interviews_for_worker(worker["id"])
    notifications = get_notifications("worker", worker["id"])

    # Attach trade visual metadata to saved jobs
    for sj in saved_jobs:
        t_meta = get_trade_for_skill(sj["skill_required"])
        sj["trade_image"] = t_meta["image"]
        sj["trade_icon"] = t_meta["icon"]
        sj["trade_color"] = t_meta["color"]

    trade_meta = get_trade_for_skill(worker["skill"])

    return render_template(
        "worker_dashboard.html",
        worker=worker,
        applications=applications,
        saved_jobs=saved_jobs,
        interviews=interviews,
        notifications=notifications,
        trade_meta=trade_meta,
        sort_by=sort_by
    )


@app.route("/worker/applications", methods=["GET", "POST"])
@worker_required
def worker_applications():
    """
    Preserve legacy route for worker applications.
    If authenticated, enforces privacy to logged-in worker by redirecting to Worker Dashboard.
    """
    return redirect(url_for("worker_dashboard"))


@app.route("/worker/profile/edit", methods=["GET", "POST"])
@worker_required
def worker_profile_edit():
    """
    Allow workers to correct their profile and preferences (Step 7).
    Instantly recalculates match scores.
    """
    worker = get_worker_by_id(session["user_id"])
    if not worker:
        flash("Worker not found.", "danger")
        return redirect(url_for("login", role="worker"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        skill = request.form.get("skill", "").strip()
        location = request.form.get("location", "").strip()
        availability = request.form.get("availability", "Immediate").strip()

        try:
            experience = int(request.form.get("experience", "0"))
            wage = int(request.form.get("wage", "0"))
        except ValueError:
            flash("Experience and wage must be valid numbers.", "danger")
            return redirect(url_for("worker_profile_edit"))

        if not all([name, skill, location]):
            flash("Please fill in all required fields.", "danger")
            return redirect(url_for("worker_profile_edit"))

        update_worker_profile(
            worker_id=worker["id"],
            name=name,
            skill=skill,
            location=location,
            experience=experience,
            wage=wage,
            availability=availability
        )

        session["name"] = name
        flash("Your profile and preferences have been updated successfully! Match scores have been refreshed.", "success")
        return redirect(url_for("worker_dashboard"))

    return render_template("worker_profile_edit.html", worker=worker)


@app.route("/employer/dashboard")
@employer_required
def employer_dashboard():
    """
    Private Employer Dashboard (Step 2):
    Company profile, verification badge, posted jobs, live applicant counts, and interviews.
    Strict privacy: employers CANNOT see other employers' applicants or private data.
    """
    with sqlite3.connect(DATABASE_NAME) as connection:
        connection.row_factory = sqlite3.Row
        employer_row = connection.execute(
            "SELECT * FROM employers WHERE id = ?", (session["user_id"],)
        ).fetchone()

    if not employer_row:
        flash("Employer session invalid. Please log in.", "danger")
        return redirect(url_for("login", role="employer"))

    employer = dict(employer_row)
    selected_status = request.args.get("status_filter", "All").strip()
    selected_job_id = request.args.get("job_id", "").strip()
    sort_by = request.args.get("sort_by", "match").strip()

    job_filter_int = int(selected_job_id) if selected_job_id.isdigit() else None
    applications = get_applications_by_employer(
        employer_email=employer["email"],
        job_id=job_filter_int,
        status_filter=selected_status if selected_status != "All" else None,
        sort_by=sort_by
    )

    with sqlite3.connect(DATABASE_NAME) as connection:
        connection.row_factory = sqlite3.Row
        employer_jobs = [dict(r) for r in connection.execute(
            """
            SELECT id, title, skill_required, description, location, workers_needed,
                   positions_remaining, daily_wage, status, created_at,
                   (SELECT COUNT(*) FROM applications WHERE job_id = jobs.id) AS total_applicants
            FROM jobs
            WHERE employer_id = ?
            ORDER BY id DESC
            """,
            (employer["id"],)
        ).fetchall()]

    interviews = get_interviews_for_employer(employer["id"])
    notifications = get_notifications("employer", employer["id"])

    # Attach trade icons
    for ej in employer_jobs:
        t_meta = get_trade_for_skill(ej["skill_required"])
        ej["trade_image"] = t_meta["image"]
        ej["trade_icon"] = t_meta["icon"]
        ej["trade_color"] = t_meta["color"]

    return render_template(
        "employer_dashboard.html",
        employer=employer,
        employer_jobs=employer_jobs,
        applications=applications,
        interviews=interviews,
        notifications=notifications,
        selected_status=selected_status,
        selected_job_id=selected_job_id,
        sort_by=sort_by
    )


@app.route("/employer/applications", methods=["GET", "POST"])
@employer_required
def employer_applications():
    """
    Preserve legacy employer applications route.
    If authenticated, enforces authorization to logged-in employer only.
    """
    # Handle status update from form if POST
    if request.method == "POST":
        action = request.form.get("action", "view").strip()
        if action == "update_status":
            try:
                application_id = int(request.form.get("application_id", ""))
                new_status = request.form.get("status", "").strip()
            except (TypeError, ValueError):
                application_id = None
                new_status = ""

            success, msg = update_application_status(application_id, new_status, session["user_id"])
            if success:
                flash(msg, "success")
            else:
                flash(msg, "danger")
    return redirect(url_for("employer_dashboard"))


@app.route("/employer/candidate-matches", methods=["GET", "POST"])
@employer_required
def candidate_matches():
    """
    Intelligent Candidate Recommendations (Step 7):
    Employers select one of their job postings and see registered workers
    ranked by compatibility score, with multilingual explanation breakdown.
    Strictly scoped to logged-in employer.
    """
    employer = None
    if session.get("user_id"):
        employer = get_employer_by_id(session["user_id"])
    if not employer and session.get("email"):
        employer = get_employer_by_email(session["email"])

    if not employer:
        flash("Employer not found.", "danger")
        return redirect(url_for("login", role="employer"))

    job_id_param = request.args.get("job_id", "").strip()
    if request.method == "POST":
        job_id_param = request.form.get("job_id", "").strip()

    with sqlite3.connect(DATABASE_NAME) as connection:
        connection.row_factory = sqlite3.Row
        employer_jobs = [dict(r) for r in connection.execute(
            "SELECT * FROM jobs WHERE employer_id = ? ORDER BY id DESC",
            (employer["id"],)
        ).fetchall()]

    selected_job = None
    matched_workers = []

    if employer_jobs:
        if job_id_param and job_id_param.isdigit():
            # Ensure the selected job belongs to this employer
            job_cand = get_job_by_id(int(job_id_param))
            if job_cand and job_cand["employer_id"] == employer["id"]:
                selected_job = job_cand
        if not selected_job:
            selected_job = employer_jobs[0]

        if selected_job:
            matched_workers = get_matched_workers_for_job(selected_job["id"], min_score=0)

    return render_template(
        "candidate_matches.html",
        employer=employer,
        employer_email=employer["email"],
        employer_jobs=employer_jobs,
        selected_job=selected_job,
        matched_workers=matched_workers
    )


# =====================================================================
# STEP 8: EXTRA FEATURES - SAVED JOBS, INTERVIEWS, VERIFICATION, REPORTS
# =====================================================================

@app.route("/jobs/<int:job_id>/save", methods=["POST"])
@worker_required
def save_job_route(job_id):
    """Save/bookmark a job for the logged-in worker."""
    success, msg = save_job_for_worker(session["user_id"], job_id)
    if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
        return jsonify({"success": success, "message": msg})
    flash(msg, "success" if success else "info")
    return redirect(request.referrer or url_for("browse_jobs"))


@app.route("/jobs/<int:job_id>/unsave", methods=["POST"])
@worker_required
def unsave_job_route(job_id):
    """Remove a bookmarked job."""
    success, msg = unsave_job_for_worker(session["user_id"], job_id)
    if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
        return jsonify({"success": success, "message": msg})
    flash(msg, "info")
    return redirect(request.referrer or url_for("worker_dashboard"))


@app.route("/employer/interviews/schedule", methods=["POST"])
@employer_required
def schedule_interview_route():
    """Schedule an interview with an applicant (Step 8)."""
    try:
        job_id = int(request.form.get("job_id", ""))
        application_id = int(request.form.get("application_id", "0"))
        worker_id = int(request.form.get("worker_id", ""))
        interview_date = request.form.get("interview_date", "").strip()
        interview_time = request.form.get("interview_time", "").strip()
        location_or_link = request.form.get("location_or_link", "").strip()
        venue = request.form.get("venue", "").strip()
        phone = request.form.get("phone", "").strip()
        notes = request.form.get("notes", "").strip()
        return_to = request.form.get("return_to", "").strip()
    except (TypeError, ValueError):
        flash("Invalid meeting parameters.", "danger")
        return redirect(url_for("employer_dashboard"))

    if not location_or_link:
        loc_parts = []
        if venue:
            loc_parts.append(venue)
        if phone:
            loc_parts.append(f"Phone: {phone}")
        location_or_link = " | ".join(loc_parts) if loc_parts else "To be coordinated"

    if not all([interview_date, interview_time, location_or_link]):
        flash("Please provide date and time for the meeting.", "danger")
        if return_to == "candidate_matches":
            return redirect(url_for("candidate_matches", job_id=job_id))
        return redirect(url_for("employer_dashboard"))

    # Enforce employer ownership of this job
    job = get_job_by_id(job_id)
    if not job or job["employer_id"] != session["user_id"]:
        flash("Unauthorized. You do not own this job.", "danger")
        if return_to == "candidate_matches":
            return redirect(url_for("candidate_matches", job_id=job_id))
        return redirect(url_for("employer_dashboard"))

    schedule_interview(
        job_id=job_id,
        application_id=application_id,
        employer_id=session["user_id"],
        worker_id=worker_id,
        interview_date=interview_date,
        interview_time=interview_time,
        location_or_link=location_or_link,
        notes=notes
    )

    flash(f"Meeting scheduled successfully for {interview_date} at {interview_time}!", "success")
    if return_to == "candidate_matches":
        return redirect(url_for("candidate_matches", job_id=job_id))
    return redirect(url_for("employer_dashboard"))


@app.route("/employer/verify", methods=["POST"])
@employer_required
def toggle_verify_route():
    """Toggle employer verified status (Step 8)."""
    toggle_employer_verification(session["user_id"])
    flash("Employer verification status updated.", "success")
    return redirect(url_for("employer_dashboard"))


@app.route("/report", methods=["POST"])
@login_required
def submit_report_route():
    """Report suspicious job or account (Step 8)."""
    target_type = request.form.get("target_type", "").strip().lower()
    try:
        target_id = int(request.form.get("target_id", ""))
    except (TypeError, ValueError):
        target_id = 0

    reason = request.form.get("reason", "").strip()
    details = request.form.get("details", "").strip()

    if not reason or not target_type or not target_id:
        flash("Please provide complete details for the report.", "warning")
        return redirect(request.referrer or url_for("home"))

    submit_report(
        reporter_role=session.get("role", "user"),
        reporter_id=session.get("user_id", 0),
        target_type=target_type,
        target_id=target_id,
        reason=reason,
        details=details
    )

    flash("Thank you for your report. Our team has recorded it to maintain trust and safety on WorkConnect.", "success")
    return redirect(request.referrer or url_for("home"))


@app.route("/api/notifications", methods=["GET"])
@login_required
def api_get_notifications():
    """Retrieve full notifications list and unread count as JSON."""
    user_role = session.get("role")
    user_id = session.get("user_id")
    notifs = get_notifications(user_role, user_id)
    unread_count = get_unread_notifications_count(user_role, user_id)
    return jsonify({
        "success": True,
        "unread_count": unread_count,
        "notifications": notifs
    })


@app.route("/api/notifications/read/<int:notif_id>", methods=["POST"])
@login_required
def api_read_notification(notif_id):
    """Mark a notification as read and return updated unread count."""
    mark_notification_as_read(notif_id, session.get("role"), session.get("user_id"))
    unread = get_unread_notifications_count(session.get("role"), session.get("user_id"))
    return jsonify({"success": True, "unread_count": unread})


@app.route("/api/notifications/read-all", methods=["POST"])
@login_required
def api_read_all_notifications():
    """Mark all notifications as read and return updated unread count."""
    mark_all_notifications_as_read(session.get("role"), session.get("user_id"))
    return jsonify({"success": True, "unread_count": 0})


# =====================================================================
# STEP 6: SERVER-SIDE AI APIS (CONVERSATIONAL AI, STT, TTS)
# =====================================================================

@app.route("/api/ai/chat", methods=["POST"])
def api_ai_chat():
    """
    Conversational AI Assistant API (Step 6).
    Handles user queries about jobs, wages, voice registration, and hiring.
    Includes cost control caching, timeouts, and multilingual domain fallbacks.
    """
    data = request.get_json(silent=True) or request.form
    message = data.get("message", "").strip()
    lang = data.get("lang") or session.get("lang", "en")
    role = session.get("role", "worker")

    if not message:
        return jsonify({"reply": "Please ask a question." if lang == "en" else "దయచేసి ఒక ప్రశ్న అడగండి."})

    try:
        reply = ask_workconnect_assistant(message, lang=lang, role=role)
        return jsonify({"reply": reply, "success": True})
    except Exception as e:
        return jsonify({
            "reply": "Service temporarily busy. Please try again." if lang == "en" else "సేవ తాత్కాలికంగా బిజీగా ఉంది.",
            "success": False
        })


@app.route("/api/voice/stt", methods=["POST"])
def api_voice_stt():
    """
    Server Speech-to-Text Parsing API (Step 4 & 6).
    Parses spoken audio transcripts to extract name, skill, location, experience, and wage.
    """
    data = request.get_json(silent=True) or request.form
    transcript = data.get("transcript", "").strip()
    lang = data.get("lang") or session.get("lang", "en")

    if not transcript:
        return jsonify({"error": "No transcript provided"}), 400

    extracted = extract_registration_fields_from_transcript(transcript, lang=lang)
    return jsonify({"success": True, "data": extracted})


@app.route("/api/voice/tts", methods=["GET", "POST"])
def api_voice_tts():
    """
    Text-to-Speech audio details helper (Step 5 & 6).
    Returns clean spoken text suitable for Web Speech synthesis in Telugu, Hindi, or English.
    """
    text = request.args.get("text") or (request.form.get("text") if request.method == "POST" else "")
    lang = request.args.get("lang") or session.get("lang", "en")

    if not text:
        return jsonify({"error": "No text provided"}), 400

    return jsonify({
        "success": True,
        "text": text,
        "lang": lang,
        "voice_locale": "te-IN" if lang == "te" else ("hi-IN" if lang == "hi" else "en-IN")
    })


if __name__ == "__main__":
    app.run(debug=True)
