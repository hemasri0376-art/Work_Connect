import re, os, sys
sys.stdout.reconfigure(encoding='utf-8')

templates_dir = 'templates'
endpoints = [
    'static', 'set_language', 'login', 'logout', 'home', 'worker_register',
    'worker_voice_register', 'employer_register', 'browse_jobs', 'post_job',
    'apply_job', 'worker_dashboard', 'worker_applications', 'worker_profile_edit',
    'employer_dashboard', 'employer_applications', 'candidate_matches',
    'save_job_route', 'unsave_job_route', 'schedule_interview_route',
    'toggle_verify_route', 'submit_report_route', 'api_read_notification',
    'api_read_all_notifications', 'api_ai_chat', 'api_voice_stt', 'api_voice_tts'
]

errors = []
for fname in os.listdir(templates_dir):
    if not fname.endswith('.html'):
        continue
    content = open(os.path.join(templates_dir, fname), encoding='utf-8').read()
    matches = re.findall(r"url_for\('([^']+)'", content)
    for ep in matches:
        if ep not in endpoints:
            errors.append(f"{fname}: url_for referencing non-existent endpoint: {ep}")

if errors:
    for e in errors:
        print("ERROR:", e)
else:
    print("All url_for references OK")
