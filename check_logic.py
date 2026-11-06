"""
Check specific logic issues in the WorkConnect project.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

issues = []

# Issue 1: app.py line 854 - uses job_id int instead of job title in flash message
with open('app.py', encoding='utf-8') as f:
    content = f.read()
    if "Remaining positions for '{job_id}'" in content:
        issues.append("app.py:854 - uses integer job_id in message string instead of job title")

# Issue 2: Check if worker_applications.html nav links are role-gated
with open('templates/worker_applications.html', encoding='utf-8') as f:
    wa = f.read()
    if "url_for('post_job')" in wa and '{% if user_role' not in wa.split("url_for('post_job')")[0].split('\n')[-5:]:
        pass  # Check context

# Issue 3: Check for match_info key consistency
# apply_job.html uses match_info['percentage'] - compute_match_score returns 'percentage' - OK
# apply_job.html uses match_info.explanation - compute_match_score returns 'explanation' - OK

# Issue 4: employer_applications redirect issue for unauthenticated users
with open('app.py', encoding='utf-8') as f:
    content = f.read()
    # Check the employer_applications route handles POST correctly
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'employer_applications' in line and 'def ' in line:
            print(f"employer_applications defined at line {i+1}")

if issues:
    for i in issues:
        print("BUG:", i)
else:
    print("Checking specific issues...")

# Check the match_info keys used in apply_job.html vs what compute_match_score returns
print("\nKeys returned by compute_match_score:")
keys = ['score', 'percentage', 'level', 'badge_class', 'reasons', 'explanation', 'breakdown']
print(keys)

print("\nKeys used in apply_job.html:")
with open('templates/apply_job.html', encoding='utf-8') as f:
    content = f.read()
    import re
    used = re.findall(r"match_info\['([^']+)'\]|match_info\.(\w+)", content)
    for bracket, dot in used:
        k = bracket or dot
        if k and k not in keys:
            print(f"  MISSING KEY: match_info['{k}'] -- not in compute_match_score output!")
        elif k:
            print(f"  OK: match_info['{k}']")
