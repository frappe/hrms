"""
Generates a fresh unique 20-character alphanumeric password for every
Employee-linked User on this site, sets it on their account, and emails it
to them.

Scope: dynamically queries the database for every Employee record that is
(a) Active and (b) linked to an enabled User -- NOT a hardcoded list. This
is intentional so it automatically covers however many users actually exist
on a given site (local test data vs. dev vs. live), instead of drifting out
of date. It will touch every matching account it finds, including ones that
already have a real password set -- review COUNT_ONLY output before ever
flipping SEND_EMAILS.

SEND_EMAILS:
  False -> sets real passwords (works anywhere), but only PREVIEWS each
           email's content instead of sending (safe on machines where the
           configured SMTP/SendGrid key doesn't authenticate).
  True  -> does the same, but actually sends via frappe.sendmail(), which
           uses the default Outgoing Email Account already configured
           (SendGrid). Only flip this on a machine where that account
           actually authenticates (currently: the GPU machine).

COUNT_ONLY:
  True  -> does nothing except print who WOULD be affected (no password
           changes, no emails). Run this first on any new environment.

Run from frappe-bench/sites:
  env/bin/python /path/to/rotate_and_email_passwords.py
"""

import frappe
import json
import secrets
import string

COUNT_ONLY = True   # run this first on a new environment -- touches nothing
SEND_EMAILS = False  # flip to True only on the machine where SMTP auth works
SITE_NAME = 'hrms.localhost'  # change to the real site name on the target machine
SITE_URL = "http://localhost:8000"  # change to the real login URL on the target machine

# Accounts to never touch even if they match the query below.
EXCLUDE_EMAILS = {"Administrator", "Guest"}

frappe.init(site=SITE_NAME)
frappe.connect()
ALPHABET = string.ascii_letters + string.digits


def get_target_users():
	"""Every enabled User linked to an Active Employee, on this site, right now."""
	rows = frappe.db.sql(
		"""
		SELECT e.user_id, e.employee_name, e.employee_number
		FROM `tabEmployee` e
		INNER JOIN `tabUser` u ON u.name = e.user_id
		WHERE e.status = 'Active'
		  AND e.user_id IS NOT NULL AND e.user_id != ''
		  AND u.enabled = 1
		ORDER BY e.employee_number
		""",
		as_dict=True,
	)
	return [r for r in rows if r.user_id not in EXCLUDE_EMAILS]


def gen_password(length=20, used=None):
	used = used or set()
	while True:
		pwd = ''.join(secrets.choice(ALPHABET) for _ in range(length))
		if pwd not in used:
			return pwd


def build_email(full_name, email, password):
	subject = "Your Clustox HRMS login"
	text = (
		f"Hi {full_name},\n\n"
		f"Your Clustox HRMS account is ready.\n\n"
		f"Login: {SITE_URL}\n"
		f"Email: {email}\n"
		f"Password: {password}\n\n"
		f"Please change your password after logging in for the first time.\n"
	)
	html = f"""
	<div style="font-family: Arial, sans-serif; max-width: 480px; margin: 0 auto;">
		<p>Hi {full_name},</p>
		<p>Your Clustox HRMS account is ready.</p>
		<p>
			<strong>Login:</strong> <a href="{SITE_URL}">{SITE_URL}</a><br>
			<strong>Email:</strong> {email}<br>
			<strong>Password:</strong> <code>{password}</code>
		</p>
		<p>Please change your password after logging in for the first time.</p>
	</div>
	"""
	return subject, text, html


targets = get_target_users()

if COUNT_ONLY:
	print("COUNT_ONLY_RESULT_START")
	print(json.dumps({
		"count": len(targets),
		"users": [{"email": t.user_id, "name": t.employee_name, "code": t.employee_number} for t in targets],
	}, indent=2))
	print("COUNT_ONLY_RESULT_END")
	raise SystemExit(0)

# --- Phase 1: generate every password up front, then hard-verify uniqueness
# across the WHOLE batch before touching a single account. If this ever
# fails, nothing has been changed and nothing has been sent yet.
used_passwords = set()
password_by_email = {}
for t in targets:
	pwd = gen_password(20, used_passwords)
	used_passwords.add(pwd)
	password_by_email[t.user_id] = pwd

all_pwds = list(password_by_email.values())
assert len(all_pwds) == len(set(all_pwds)), (
	"Password uniqueness check failed -- aborting before any account was touched."
)
assert all(len(p) == 20 for p in all_pwds), "Password length check failed -- aborting."
print(f"UNIQUENESS_CHECK_PASSED: {len(all_pwds)} passwords, all unique, all 20 characters.")

# --- Phase 2: apply. Each password was already generated + verified above,
# so this loop only sets/sends -- it never generates a password itself.
results = []
audit = []  # kept local only, never printed

for t in targets:
	email = t.user_id
	pwd = password_by_email[email]
	record = {"email": email, "employee": t.employee_number}
	try:
		user = frappe.get_doc("User", email)
		full_name = user.full_name or t.employee_name or email

		user.new_password = pwd
		user.send_welcome_email = 0
		user.save(ignore_permissions=True)
		record["password_set"] = True

		subject, text, html = build_email(full_name, email, pwd)
		audit.append({"email": email, "password": pwd})

		if SEND_EMAILS:
			frappe.sendmail(recipients=[email], subject=subject, message=html, now=True)
			record["status"] = "SENT"
		else:
			record["status"] = "DRY_RUN_PREVIEW"
			record["preview_subject"] = subject
			record["preview_text"] = text

		results.append(record)
	except Exception as e:
		record["status"] = "ERROR"
		record["error"] = str(e)
		results.append(record)

frappe.db.commit()

# Audit file kept local for our own recovery only -- never printed to logs/chat.
# Delete this file once you've confirmed all emails arrived correctly.
with open('password_audit_DO_NOT_SHARE.json', 'w') as f:
	json.dump(audit, f, indent=2)

# Printed summary intentionally omits password values.
summary = [{k: v for k, v in r.items() if k not in ("preview_text",)} for r in results]
print("ROTATE_RESULT_START")
print(json.dumps(summary, indent=2))
print("ROTATE_RESULT_END")

if not SEND_EMAILS and results:
	print("SAMPLE_EMAIL_PREVIEW_START")
	print(results[0].get("preview_text", "(no preview available)"))
	print("SAMPLE_EMAIL_PREVIEW_END")
