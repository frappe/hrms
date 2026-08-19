import frappe
import json

SITE_NAME = 'hrms.localhost'  # change to the real site name on the target machine
CONFIG_PATH = 'smtp_config.json'  # keep this file next to the script, never commit it

frappe.init(site=SITE_NAME)
frappe.connect()
frappe.flags.mute_emails = True

with open(CONFIG_PATH) as f:
	cfg = json.load(f)

RESULT = {}

existing_name = frappe.db.get_value("Email Account", {"email_id": cfg["email_id"]}, "name")
if existing_name:
	acc = frappe.get_doc("Email Account", existing_name)
else:
	acc = frappe.new_doc("Email Account")
	acc.email_id = cfg["email_id"]
	acc.email_account_name = "Clustox HRMS Outgoing (SendGrid)"

acc.enable_outgoing = 1
acc.smtp_server = cfg["smtp_server"]
acc.smtp_port = cfg["smtp_port"]
acc.use_tls = 1
acc.auth_method = "Basic"
acc.login_id_is_different = 1
acc.login_id = cfg["login_id"]
acc.password = cfg["password"]
acc.default_outgoing = 1
acc.always_use_account_email_id_as_sender = 1
acc.save(ignore_permissions=True)
frappe.db.commit()

RESULT["email_account"] = acc.name
RESULT["enable_outgoing"] = acc.enable_outgoing
RESULT["default_outgoing"] = acc.default_outgoing
RESULT["smtp_server"] = acc.smtp_server
RESULT["smtp_port"] = acc.smtp_port

print("SMTP_CONFIG_RESULT_START")
print(json.dumps(RESULT, indent=2, default=str))
print("SMTP_CONFIG_RESULT_END")
