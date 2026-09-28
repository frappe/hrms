"""First-employees setup: lets HR add the first few employees from a dialog, by dropping an
employee export from Excel, Keka or greytHR, pasting rows from a spreadsheet, typing them in,
or starting with demo employees."""

import re
from datetime import date, datetime

import frappe
from frappe import _
from frappe.utils import add_months, add_years, cint, cstr, getdate

MIN_EMPLOYEES = 3
SETUP_ROLES = ("HR Manager", "System Manager")

# canonical field -> header aliases (normalized: lowercase, alphanumerics and spaces only)
FIELD_ALIASES = {
	"employee_number": [
		"employee number",
		"employee no",
		"employee id",
		"emp id",
		"emp no",
		"employee code",
		"emp code",
		"staff id",
		"id",
	],
	"employee_name": ["employee name", "full name", "name", "display name"],
	"first_name": ["first name", "given name"],
	"middle_name": ["middle name"],
	"last_name": ["last name", "surname", "family name"],
	"email": [
		"work email",
		"email",
		"email id",
		"official email",
		"company email",
		"email address",
		"user id",
		"login",
	],
	"gender": ["gender", "sex"],
	"date_of_birth": ["date of birth", "dob", "birth date", "birthday"],
	"date_of_joining": [
		"date of joining",
		"doj",
		"joining date",
		"date of join",
		"join date",
		"hire date",
		"start date",
	],
	"department": ["department", "dept"],
	"designation": ["designation", "job title", "title", "position"],
	"reports_to": [
		"reports to",
		"reporting manager",
		"reporting manager name",
		"reporting to",
		"manager",
		"manager name",
		"supervisor",
	],
	"cell_number": [
		"mobile",
		"mobile number",
		"mobile phone",
		"phone",
		"phone number",
		"contact number",
		"cell number",
	],
	"company": ["company", "legal entity", "entity"],
}

FIELD_LABELS = {
	"employee_number": "Employee Number",
	"employee_name": "Full Name",
	"first_name": "First Name",
	"middle_name": "Middle Name",
	"last_name": "Last Name",
	"email": "Email (creates login)",
	"gender": "Gender",
	"date_of_birth": "Date of Birth",
	"date_of_joining": "Date of Joining",
	"department": "Department",
	"designation": "Designation",
	"reports_to": "Reports To",
	"cell_number": "Mobile Number",
	"company": "Company",
}

REQUIRED_FIELDS = ("gender", "date_of_birth", "date_of_joining")

# demo employees have no email, so no logins are created for them
DEMO_EMPLOYEES = [
	{
		"employee_name": "Aarav Mehta",
		"gender": "Male",
		"age": 41,
		"months_since_joining": 36,
		"department": "Management",
		"designation": "Head of Operations",
		"reports_to": "",
	},
	{
		"employee_name": "Priya Nair",
		"gender": "Female",
		"age": 34,
		"months_since_joining": 24,
		"department": "Engineering",
		"designation": "Engineering Manager",
		"reports_to": "Aarav Mehta",
	},
	{
		"employee_name": "Rahul Verma",
		"gender": "Male",
		"age": 29,
		"months_since_joining": 14,
		"department": "Engineering",
		"designation": "Software Engineer",
		"reports_to": "Priya Nair",
	},
	{
		"employee_name": "Sneha Iyer",
		"gender": "Female",
		"age": 27,
		"months_since_joining": 8,
		"department": "Engineering",
		"designation": "Software Engineer",
		"reports_to": "Priya Nair",
	},
	{
		"employee_name": "Karan Shah",
		"gender": "Male",
		"age": 31,
		"months_since_joining": 5,
		"department": "Sales",
		"designation": "Account Executive",
		"reports_to": "Aarav Mehta",
	},
]

# a layout is recognised when most of its signature headers are present
LAYOUTS = {
	"Keka": ["employee number", "employee name", "work email", "job title", "reporting manager"],
	"greytHR": ["employee no", "employee name", "email", "date of join", "designation"],
	"Frappe HR": ["first name", "gender", "date of birth", "date of joining", "company"],
}


def normalize_header(header) -> str:
	text = cstr(header).strip().lower()
	text = re.sub(r"\(.*?\)", " ", text)
	text = re.sub(r"[^a-z0-9 ]+", " ", text)
	return re.sub(r"\s+", " ", text).strip()


def has_setup_role() -> bool:
	return bool(set(SETUP_ROLES) & set(frappe.get_roles()))


def get_active_employee_count() -> int:
	return frappe.db.count("Employee", {"status": "Active"})


@frappe.whitelist()
def get_setup_status() -> dict:
	"""Cheap enough to sit in boot info: one count plus the company list."""
	if not has_setup_role() or not frappe.is_setup_complete():
		return {"show": 0}

	active = get_active_employee_count()
	companies = frappe.get_all("Company", pluck="name", order_by="creation asc")
	session_data = frappe.session.get("data") or {}
	return {
		"show": int(active < MIN_EMPLOYEES),
		"active_employees": active,
		"required": MIN_EMPLOYEES,
		"companies": companies,
		# "Later" is remembered per login; a fresh session brings the dialog back
		"session": f"{frappe.session.user}|{session_data.get('creation') or ''}",
		"default_company": frappe.defaults.get_user_default("Company")
		or (companies[0] if len(companies) == 1 else None),
	}


@frappe.whitelist()
def create_employees(rows: list | str, company: str | None = None) -> dict:
	"""Create one Employee per row. Rows that fail are reported, not raised, so the rest go through.

	Each row: employee_name (or first_name/last_name), email, gender, date_of_birth, date_of_joining,
	and optionally employee_number, department, designation, reports_to, cell_number, company."""
	frappe.only_for(list(SETUP_ROLES))
	rows = frappe.parse_json(rows) if isinstance(rows, str) else rows
	company = company or get_setup_status().get("default_company")

	created, errors, incomplete = [], [], []
	pending_managers = []

	for index, raw in enumerate(rows):
		row = frappe._dict(raw)
		row_number = row.get("row_number") or index + 1
		if not any(cstr(v).strip() for v in row.values()):
			continue

		frappe.db.savepoint("employee_setup_row")
		try:
			if not cstr(row.get("date_of_birth")).strip() and cstr(row.get("age")).strip():
				row.date_of_birth = date_of_birth_from_age(row.age)
			missing = [FIELD_LABELS[f] for f in REQUIRED_FIELDS if not cstr(row.get(f)).strip()]
			if not (cstr(row.get("employee_name")).strip() or cstr(row.get("first_name")).strip()):
				missing.insert(0, FIELD_LABELS["employee_name"])
			if missing:
				incomplete.append({"row_number": row_number, "row": raw, "missing": missing})
				continue

			employee = make_employee(row, company)
			created.append(
				{
					"row_number": row_number,
					"name": employee.name,
					"employee_name": employee.employee_name,
					"user_id": employee.user_id,
				}
			)
			if cstr(row.get("reports_to")).strip():
				pending_managers.append((employee.name, cstr(row.reports_to).strip()))
		except Exception as e:
			frappe.db.rollback(save_point="employee_setup_row")
			errors.append({"row_number": row_number, "row": raw, "message": cstr(e)})

	unresolved_managers = link_reports_to(pending_managers)

	return {
		"created": created,
		"errors": errors,
		"incomplete": incomplete,
		"unresolved_managers": unresolved_managers,
		"active_employees": get_active_employee_count(),
		"required": MIN_EMPLOYEES,
	}


def make_employee(row, default_company: str | None):
	first, middle, last = split_name(row)
	company = cstr(row.get("company")).strip() or default_company
	if not company:
		frappe.throw(_("Company is required"))
	if not frappe.db.exists("Company", company):
		frappe.throw(_("Company {0} does not exist").format(company))

	naming_method = frappe.db.get_single_value("HR Settings", "emp_created_by")
	employee_number = cstr(row.get("employee_number")).strip()
	if naming_method == "Employee Number" and not employee_number:
		frappe.throw(_("Employee Number is required because HR Settings names employees by number"))

	employee = frappe.new_doc("Employee")
	employee.update(
		{
			"first_name": first,
			"middle_name": middle,
			"last_name": last,
			"company": company,
			"status": "Active",
			"gender": get_or_create_gender(row.gender),
			"date_of_birth": parse_date(row.date_of_birth, FIELD_LABELS["date_of_birth"]),
			"date_of_joining": parse_date(row.date_of_joining, FIELD_LABELS["date_of_joining"]),
			"employee_number": employee_number or None,
			"cell_number": cstr(row.get("cell_number")).strip() or None,
		}
	)

	email = cstr(row.get("email")).strip().lower()
	if email:
		employee.user_id = get_or_create_user(email, first, middle, last)
		employee.company_email = email
	if department := cstr(row.get("department")).strip():
		employee.department = get_or_create_department(department, company)
	if designation := cstr(row.get("designation")).strip():
		employee.designation = get_or_create_designation(designation)

	employee.flags.ignore_permissions = True
	employee.insert()
	return employee


def split_name(row) -> tuple[str, str | None, str | None]:
	first = cstr(row.get("first_name")).strip()
	if first:
		return (
			first,
			cstr(row.get("middle_name")).strip() or None,
			cstr(row.get("last_name")).strip() or None,
		)

	parts = cstr(row.get("employee_name")).split()
	if not parts:
		frappe.throw(_("Name is required"))
	if len(parts) == 1:
		return parts[0], None, None
	if len(parts) == 2:
		return parts[0], None, parts[1]
	return parts[0], " ".join(parts[1:-1]), parts[-1]


def parse_date(value, label: str):
	if isinstance(value, datetime):
		return value.date()
	if isinstance(value, date):
		return value

	text = cstr(value).strip()
	if not text:
		frappe.throw(_("{0} is required").format(label))

	from dateutil import parser

	# numeric dates like 12/04/1990 are ambiguous: follow the site's date format
	if re.match(r"^\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}$", text):
		dayfirst = not cstr(frappe.get_system_settings("date_format")).lower().startswith("mm")
		try:
			return parser.parse(text, dayfirst=dayfirst).date()
		except (ValueError, OverflowError):
			frappe.throw(_("Could not read {0} '{1}'").format(label, text))

	try:
		return getdate(text)
	except Exception:
		pass

	try:
		return parser.parse(text, dayfirst=True).date()
	except (ValueError, OverflowError):
		frappe.throw(_("Could not read {0} '{1}'").format(label, text))


def date_of_birth_from_age(age) -> date:
	"""Approximate: today's month and day, `age` years back. Meant to be corrected later."""
	years = cint(age)
	if years <= 0 or years > 120:
		frappe.throw(_("Approximate age must be between 1 and 120"))
	return add_years(getdate(), -years)


def get_or_create_gender(value) -> str:
	text = cstr(value).strip()
	if not text:
		frappe.throw(_("Gender is required"))

	aliases = {"m": "Male", "male": "Male", "f": "Female", "female": "Female", "o": "Other", "other": "Other"}
	name = aliases.get(text.lower())
	if not name:
		name = frappe.db.get_value("Gender", {"name": ("like", text)}) or text.title()
	if not frappe.db.exists("Gender", name):
		frappe.get_doc({"doctype": "Gender", "gender": name}).insert(ignore_permissions=True)
	return name


def get_or_create_user(email: str, first: str, middle: str | None, last: str | None) -> str:
	if frappe.db.exists("User", email):
		return email

	send_welcome_email = bool(
		frappe.db.exists("Email Account", {"enable_outgoing": 1, "default_outgoing": 1})
	)
	user = frappe.get_doc(
		{
			"doctype": "User",
			"email": email,
			"first_name": first,
			"middle_name": middle,
			"last_name": last,
			"user_type": "System User",
			"send_welcome_email": int(send_welcome_email),
		}
	)
	# the Employee role is added by Employee.update_user once the link exists; adding it
	# earlier makes ERPNext strip it again with a "no mapped employee" message
	user.flags.ignore_permissions = True
	user.flags.no_welcome_mail = not send_welcome_email
	user.insert()
	# Frappe warns about a role-less user here; the Employee record adds the role a moment later
	frappe.local.message_log = [
		m for m in frappe.get_message_log() if m.get("title") != _("No Roles Specified")
	]
	return user.name


def get_or_create_department(name: str, company: str) -> str:
	existing = frappe.db.get_value("Department", {"department_name": name, "company": company})
	if existing:
		return existing
	doc = frappe.get_doc({"doctype": "Department", "department_name": name, "company": company})
	doc.insert(ignore_permissions=True)
	return doc.name


def get_or_create_designation(name: str) -> str:
	existing = frappe.db.get_value("Designation", {"designation_name": name})
	if existing:
		return existing
	doc = frappe.get_doc({"doctype": "Designation", "designation_name": name})
	doc.insert(ignore_permissions=True)
	return doc.name


def link_reports_to(pending: list[tuple[str, str]]) -> list[dict]:
	"""Managers are matched by employee name, employee number or email once every row exists,
	so the order of rows in a file does not matter."""
	unresolved = []
	for employee, manager in pending:
		manager_id = find_employee(manager)
		if manager_id and manager_id != employee:
			frappe.db.set_value("Employee", employee, "reports_to", manager_id)
		else:
			unresolved.append({"employee": employee, "reports_to": manager})
	return unresolved


def find_employee(text: str) -> str | None:
	text = text.strip()
	if not text:
		return None
	for field in ("name", "employee_number", "user_id", "company_email", "employee_name"):
		match = frappe.db.get_value("Employee", {field: text, "status": "Active"})
		if match:
			return match
	return None


@frappe.whitelist()
def get_demo_employees() -> list[dict]:
	"""Demo rows with dates worked out relative to today, so they never go stale."""
	frappe.only_for(list(SETUP_ROLES))
	rows = []
	for demo in DEMO_EMPLOYEES:
		row = {k: v for k, v in demo.items() if k not in ("age", "months_since_joining")}
		row["date_of_birth"] = date_of_birth_from_age(demo["age"])
		row["date_of_joining"] = add_months(getdate(), -demo["months_since_joining"])
		rows.append(row)
	return rows


@frappe.whitelist()
def create_demo_employees(company: str | None = None) -> dict:
	frappe.only_for(list(SETUP_ROLES))
	return create_employees(get_demo_employees(), company)


@frappe.whitelist()
def detect_employee_file(file_url: str) -> dict:
	"""Read the header row, guess the source system, and propose a column map."""
	frappe.only_for(list(SETUP_ROLES))
	return detect_rows(read_rows(file_url))


@frappe.whitelist()
def detect_pasted_employees(content: str) -> dict:
	"""Same as `detect_employee_file` for rows copied from a spreadsheet or CSV."""
	frappe.only_for(list(SETUP_ROLES))
	return detect_rows(parse_pasted_rows(content))


def detect_rows(rows: list[list]) -> dict:
	if not rows:
		frappe.throw(_("There are no rows to read"))

	headers = [cstr(h).strip() for h in rows[0]]
	normalized = [normalize_header(h) for h in headers]

	layout, score = None, 0
	for name, signature in LAYOUTS.items():
		hits = sum(1 for s in signature if s in normalized)
		ratio = hits / len(signature)
		if ratio > score:
			layout, score = name, ratio
	if score < 0.6:
		layout = None

	columns = [{"header": h, "field": guess_field(n)} for h, n in zip(headers, normalized, strict=False)]
	data_rows = [r for r in rows[1:] if any(cstr(v).strip() for v in r)]

	return {
		"layout": layout,
		"columns": columns,
		"fields": [{"value": k, "label": v} for k, v in FIELD_LABELS.items()],
		"row_count": len(data_rows),
		"sample": [[cstr(v) for v in r] for r in data_rows[:3]],
	}


def guess_field(normalized_header: str) -> str:
	if not normalized_header:
		return ""
	for field, aliases in FIELD_ALIASES.items():
		if normalized_header in aliases:
			return field
	for field, aliases in FIELD_ALIASES.items():
		for alias in aliases:
			if len(alias) > 3 and alias in normalized_header:
				return field
	return ""


@frappe.whitelist()
def import_employees(file_url: str, column_map: dict | str, company: str | None = None) -> dict:
	"""column_map: {header: field}. Headers mapped to "" are skipped."""
	frappe.only_for(list(SETUP_ROLES))
	return import_rows(read_rows(file_url), column_map, company)


@frappe.whitelist()
def import_pasted_employees(content: str, column_map: dict | str, company: str | None = None) -> dict:
	frappe.only_for(list(SETUP_ROLES))
	return import_rows(parse_pasted_rows(content), column_map, company)


def import_rows(rows: list[list], column_map: dict | str, company: str | None = None) -> dict:
	column_map = frappe.parse_json(column_map) if isinstance(column_map, str) else column_map
	if len(rows) < 2:
		frappe.throw(_("There is a header row but no employees"))

	headers = [cstr(h).strip() for h in rows[0]]
	fields = [column_map.get(h) or "" for h in headers]

	employees = []
	for index, raw in enumerate(rows[1:], start=2):
		if not any(cstr(v).strip() for v in raw):
			continue
		row = {"row_number": index}
		for field, value in zip(fields, raw, strict=False):
			if field and value not in (None, ""):
				row[field] = value.isoformat() if isinstance(value, datetime | date) else value
		employees.append(row)

	return create_employees(employees, company)


def read_rows(file_url: str) -> list[list]:
	file_doc = frappe.get_doc("File", {"file_url": file_url})
	extension = (file_doc.file_name or file_url).rsplit(".", 1)[-1].lower()

	if extension == "xlsx":
		from frappe.utils.xlsxutils import read_xlsx_file_from_attached_file

		rows = read_xlsx_file_from_attached_file(file_url=file_url)
	elif extension == "xls":
		from frappe.utils.xlsxutils import read_xls_file_from_attached_file

		rows = read_xls_file_from_attached_file(file_doc.get_content())
	elif extension in ("csv", "txt"):
		from frappe.utils.csvutils import read_csv_content

		rows = read_csv_content(file_doc.get_content(), use_sniffer=True)
	else:
		frappe.throw(_("Upload an .xlsx, .xls or .csv file"))

	return drop_leading_blank_rows(rows)


def parse_pasted_rows(content: str) -> list[list]:
	"""Rows copied from Excel or Google Sheets arrive tab separated; anything else is read as CSV."""
	from frappe.utils.csvutils import read_csv_content

	text = cstr(content).replace("\r\n", "\n").replace("\r", "\n").strip("\n")
	if not text.strip():
		frappe.throw(_("Paste a few rows first, including the header row"))

	lines = text.split("\n")
	if "\t" in lines[0]:
		rows = [line.split("\t") for line in lines]
	else:
		rows = read_csv_content(text, use_sniffer=True)

	return drop_leading_blank_rows(rows)


def drop_leading_blank_rows(rows: list[list]) -> list[list]:
	while rows and not any(cstr(v).strip() for v in rows[0]):
		rows.pop(0)
	return rows or []


@frappe.whitelist()
def get_next_steps() -> list[dict]:
	"""What usually blocks the first leave application once employees exist."""
	frappe.only_for(list(SETUP_ROLES))
	steps = []

	without_approver = frappe.db.count("Employee", {"status": "Active", "leave_approver": ("in", ("", None))})
	if without_approver:
		steps.append(
			{
				"title": _("Set a Leave Approver"),
				"description": _("{0} employees have none").format(without_approver),
				"route": ["List", "Employee", {"status": "Active", "leave_approver": ["is", "not set"]}],
			}
		)

	year = getdate().year
	if not frappe.db.exists(
		"Holiday List", {"from_date": ("<=", f"{year}-12-31"), "to_date": (">=", f"{year}-01-01")}
	):
		steps.append(
			{
				"title": _("Create a Holiday List"),
				"description": _("None covers {0} yet").format(year),
				"route": ["Form", "Holiday List", "new"],
			}
		)

	if not frappe.db.count("Leave Policy Assignment", {"docstatus": 1}):
		steps.append(
			{
				"title": _("Allocate leaves"),
				"description": _("Assign a Leave Policy so balances exist"),
				"route": ["Form", "Leave Policy Assignment", "new"],
			}
		)

	return steps
