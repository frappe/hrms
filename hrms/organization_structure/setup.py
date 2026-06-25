# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Sample data and role setup for the Organization Structure module.

Run from the bench:

	bench --site <site> execute hrms.organization_structure.setup.create_sample_data

This is idempotent and safe to run multiple times.
"""

from pathlib import Path

import frappe
from frappe.modules.import_file import import_file_by_path

# Job categories follow the ownership template: each organization unit type is
# owned (headed) by a position of the corresponding category.
JOB_CATEGORIES = [
	"Chief Executive Officer",
	"Chief Officer",
	"Vice President",
	"Senior Director",
	"Director",
	"Senior Manager",
	"Manager",
	"Professional",
	"Semi-Professional",
	"Manual Custodian",
]

# Job grade levels as roman numerals (I = most senior).
JOB_GRADES = ["I", "II", "III", "IV", "V", "VI", "VII"]

# (template_name, template_code, job_grade, position_family, job_category)
POSITION_TEMPLATES = [
	("Chief Executive Officer", "CEO", "I", "Executive", "Chief Executive Officer"),
	("Chief Technology Officer", "CTO", "I", "Executive", "Chief Officer"),
	("Chief Financial Officer", "CFO", "I", "Executive", "Chief Officer"),
	("Chief People Officer", "CPO", "I", "Executive", "Chief Officer"),
	("Director", "DIR", "II", "Management", "Director"),
	("Development Manager", "DM", "III", "Technology", "Manager"),
	("Senior Software Engineer", "SSE", "IV", "Technology", "Professional"),
	("Software Engineer", "SE", "V", "Technology", "Professional"),
	("Branch Manager", "BM", "III", "Banking Operations", "Manager"),
	("Customer Service Officer", "CSO", "V", "Banking Operations", "Professional"),
	("Teller", "TEL", "VI", "Banking Operations", "Semi-Professional"),
	("Security Guard", "SG", "VII", "Security", "Manual Custodian"),
]

# (template_name, branch_type, [(position_template, quantity), ...])
BRANCH_STAFFING_TEMPLATES = [
	(
		"Small Branch",
		"Small",
		[("Branch Manager", 1), ("Customer Service Officer", 2), ("Teller", 3), ("Security Guard", 2)],
	),
	(
		"Medium Branch",
		"Medium",
		[("Branch Manager", 1), ("Customer Service Officer", 3), ("Teller", 5), ("Security Guard", 2)],
	),
	(
		"Large Branch",
		"Large",
		[("Branch Manager", 1), ("Customer Service Officer", 5), ("Teller", 8), ("Security Guard", 3)],
	),
]

# (region_name, region_code)
REGIONS = [
	("Addis Ababa", "AA"),
	("Oromia", "OR"),
	("Amhara", "AM"),
	("Sidama", "SD"),
	("Dire Dawa", "DD"),
]

# (zone_name, zone_code, region)
ZONES = [
	("Bole", "BOL-Z", "Addis Ababa"),
	("Yeka", "YEK", "Addis Ababa"),
	("Arada", "ARD", "Addis Ababa"),
	("East Shewa", "ESH", "Oromia"),
	("West Arsi", "WAR", "Oromia"),
	("Sidama Zone", "SDZ", "Sidama"),
]

# (city_name, city_code, region, zone)
CITIES = [
	("Addis Ababa", "AA-CITY", "Addis Ababa", "Bole"),
	("Adama", "ADA-C", "Oromia", "East Shewa"),
	("Jimma", "JIM-C", "Oromia", "West Arsi"),
	("Nekemte", "NEK-C", "Oromia", "West Arsi"),
	("Hawassa", "HAW", "Sidama", "Sidama Zone"),
]

# (woreda_name, woreda_code, city)
WOREDAS = [
	("Woreda 01", "W01", "Addis Ababa"),
	("Woreda 03", "W03", "Addis Ababa"),
	("Woreda 10", "W10", "Addis Ababa"),
	("Adama Woreda", "ADW", "Adama"),
	("Jimma Woreda", "JIW", "Jimma"),
	("Nekemte Woreda", "NEW", "Nekemte"),
]

# (unit_name, unit_code, unit_type, parent, is_group, location_1, region, zone, city, woreda, address, staffing, is_primary_ho)
SITE_ORGANIZATION_UNITS = [
	(
		"Head Office",
		"HQ",
		"Executive",
		"Executive Office",
		1,
		"Head Office",
		"Addis Ababa",
		"Bole",
		"Addis Ababa",
		"Woreda 01",
		"Churchill Avenue",
		None,
		1,
	),
	(
		"Addis District",
		"ADD",
		"District",
		"Head Office",
		1,
		"District Office",
		"Addis Ababa",
		"Yeka",
		None,
		None,
		None,
		None,
		0,
	),
	(
		"Bole Branch",
		"BOL",
		"Branch",
		"Addis District",
		0,
		"Branch",
		"Addis Ababa",
		"Bole",
		"Addis Ababa",
		"Woreda 03",
		"Bole Road",
		"Medium Branch",
		0,
	),
	(
		"Megenagna Branch",
		"MEG",
		"Branch",
		"Addis District",
		0,
		"Branch",
		"Addis Ababa",
		"Yeka",
		None,
		None,
		"Megenagna",
		"Small Branch",
		0,
	),
	(
		"Sarbet Branch",
		"SAR",
		"Branch",
		"Addis District",
		0,
		"Branch",
		"Addis Ababa",
		"Bole",
		"Addis Ababa",
		"Woreda 01",
		"Sarbet",
		"Small Branch",
		0,
	),
	(
		"Oromia District",
		"ORD",
		"District",
		"Head Office",
		1,
		"District Office",
		"Oromia",
		"East Shewa",
		None,
		None,
		None,
		None,
		0,
	),
	(
		"Adama Branch",
		"ADA",
		"Branch",
		"Oromia District",
		0,
		"Branch",
		"Oromia",
		"East Shewa",
		"Adama",
		"Adama Woreda",
		"Adama Main Street",
		"Large Branch",
		0,
	),
	(
		"Jimma Branch",
		"JIM",
		"Branch",
		"Oromia District",
		0,
		"Branch",
		"Oromia",
		"West Arsi",
		"Jimma",
		"Jimma Woreda",
		"Jimma",
		"Small Branch",
		0,
	),
	(
		"Nekemte Branch",
		"NEK",
		"Branch",
		"Oromia District",
		0,
		"Branch",
		"Oromia",
		"West Arsi",
		"Nekemte",
		"Nekemte Woreda",
		"Nekemte",
		"Small Branch",
		0,
	),
]

# Legacy alias kept for HQ position sample data.
HEAD_OFFICE_SITE = "Head Office"

LOCATION_1_FROM_LEGACY = {
	"Head Office": "Head Office",
	"District": "District Office",
	"Branch": "Branch",
}

# (unit_name, unit_code, unit_type, parent, is_group)
ORGANIZATION_UNITS = [
	("Executive Office", "EXEC", "Executive", None, 1),
	("People Function", "FUNC-PPL", "Function", "Executive Office", 1),
	("Growth and Operations", "PROC-GO", "Process", "People Function", 1),
	("Products", "SUBP-PRD", "Sub-Process", "Growth and Operations", 1),
	("Corporate Banking", "DEPT-CB", "Department", "Products", 1),
	("Import", "TEAM-IMP", "Team", "Corporate Banking", 1),
	("Documentation", "SUBT-DOC", "Sub-Team", "Import", 0),
	("Export", "TEAM-EXP", "Team", "Corporate Banking", 0),
	("Retail Banking", "DEPT-RB", "Department", "Products", 0),
	("Services", "SUBP-SVC", "Sub-Process", "Growth and Operations", 0),
	("Talent Management", "PROC-TM", "Process", "People Function", 0),
	("Finance Function", "FUNC-FIN", "Function", "Executive Office", 0),
]

# Head-office reporting tree (independent from the organization tree).
# (position_code, position_template, organization_unit, parent_code, is_group, is_head)
HQ_POSITIONS = [
	("CEO-HQ-001", "Chief Executive Officer", "Executive Office", None, 1, 1),
	("CFO-HQ-001", "Chief Financial Officer", "Finance Function", "CEO-HQ-001", 0, 1),
	("CPO-HQ-001", "Chief People Officer", "People Function", "CEO-HQ-001", 1, 1),
	("CTO-HQ-001", "Chief Technology Officer", "Growth and Operations", "CEO-HQ-001", 1, 1),
	("DIR-HQ-001", "Director", "Products", "CTO-HQ-001", 1, 1),
	("DM-HQ-001", "Development Manager", "Corporate Banking", "DIR-HQ-001", 1, 1),
	("SSE-HQ-001", "Senior Software Engineer", "Import", "DM-HQ-001", 0, 0),
	("SE-HQ-001", "Software Engineer", "Import", "DM-HQ-001", 0, 0),
]

HEAD_OFFICE_LOCATION = HEAD_OFFICE_SITE


def create_roles():
	if not frappe.db.exists("Role", "Organization Administrator"):
		frappe.get_doc(
			{
				"doctype": "Role",
				"role_name": "Organization Administrator",
				"desk_access": 1,
			}
		).insert(ignore_permissions=True)


def create_job_categories():
	for category_name in JOB_CATEGORIES:
		if not frappe.db.exists("Job Category", category_name):
			frappe.get_doc(
				{"doctype": "Job Category", "job_category_name": category_name}
			).insert(ignore_permissions=True)


def create_job_grades():
	for grade_level in JOB_GRADES:
		if not frappe.db.exists("Job Grade", grade_level):
			frappe.get_doc(
				{"doctype": "Job Grade", "grade_level": grade_level}
			).insert(ignore_permissions=True)


def create_position_templates():
	for template_name, template_code, job_grade, position_family, job_category in POSITION_TEMPLATES:
		if frappe.db.exists("Position Template", template_name):
			continue

		frappe.get_doc(
			{
				"doctype": "Position Template",
				"template_name": template_name,
				"template_code": template_code,
				"job_grade": job_grade,
				"job_category": job_category,
				"position_family": position_family,
			}
		).insert(ignore_permissions=True)


def create_branch_staffing_templates():
	for template_name, branch_type, rows in BRANCH_STAFFING_TEMPLATES:
		if frappe.db.exists("Branch Staffing Template", template_name):
			continue

		frappe.get_doc(
			{
				"doctype": "Branch Staffing Template",
				"template_name": template_name,
				"branch_type": branch_type,
				"staffing_details": [
					{"position_template": template, "quantity": qty} for template, qty in rows
				],
			}
		).insert(ignore_permissions=True)


def create_organization_units():
	for unit_name, unit_code, unit_type, parent, is_group in ORGANIZATION_UNITS:
		if frappe.db.exists("Organization Unit", unit_name):
			continue

		frappe.get_doc(
			{
				"doctype": "Organization Unit",
				"unit_name": unit_name,
				"unit_code": unit_code,
				"unit_type": unit_type,
				"parent_organization_unit": parent,
				"is_group": is_group,
				"status": "Active",
			}
		).insert(ignore_permissions=True)


def create_regions():
	for region_name, region_code in REGIONS:
		if frappe.db.exists("Region", region_name):
			continue
		frappe.get_doc(
			{
				"doctype": "Region",
				"region_name": region_name,
				"region_code": region_code,
				"status": "Active",
			}
		).insert(ignore_permissions=True)


def create_zones():
	for zone_name, zone_code, region in ZONES:
		if frappe.db.exists("Zone", zone_name):
			continue
		frappe.get_doc(
			{
				"doctype": "Zone",
				"zone_name": zone_name,
				"zone_code": zone_code,
				"region": region,
				"status": "Active",
			}
		).insert(ignore_permissions=True)


def create_cities():
	for city_name, city_code, region, zone in CITIES:
		if frappe.db.exists("City", city_name):
			continue
		frappe.get_doc(
			{
				"doctype": "City",
				"city_name": city_name,
				"city_code": city_code,
				"region": region,
				"zone": zone,
				"status": "Active",
			}
		).insert(ignore_permissions=True)


def create_woredas():
	for woreda_name, woreda_code, city in WOREDAS:
		if frappe.db.exists("Woreda", woreda_name):
			continue
		frappe.get_doc(
			{
				"doctype": "Woreda",
				"woreda_name": woreda_name,
				"woreda_code": woreda_code,
				"city": city,
				"status": "Active",
			}
		).insert(ignore_permissions=True)


def create_site_organization_units():
	"""Create physical sites as organization units. Branches auto-generate positions on insert."""
	for (
		unit_name,
		unit_code,
		unit_type,
		parent,
		is_group,
		location_1,
		region,
		zone,
		city,
		woreda,
		address_line_1,
		staffing,
		is_primary_ho,
	) in SITE_ORGANIZATION_UNITS:
		payload = {
			"unit_code": unit_code,
			"unit_type": unit_type,
			"parent_organization_unit": parent,
			"is_group": is_group,
			"status": "Active",
			"location_1": location_1,
			"is_primary_head_office": is_primary_ho,
			"region": region,
			"zone": zone,
			"city": city,
			"woreda": woreda,
			"address_line_1": address_line_1,
			"branch_staffing_template": staffing,
			"auto_create_positions": 1 if staffing else 0,
		}

		if frappe.db.exists("Organization Unit", unit_name):
			existing = frappe.db.get_value("Organization Unit", unit_name, "location_1")
			if existing:
				continue
			frappe.db.set_value("Organization Unit", unit_name, payload, update_modified=False)
			continue

		frappe.get_doc({"doctype": "Organization Unit", "unit_name": unit_name, **payload}).insert(
			ignore_permissions=True
		)


def create_location_units():
	"""Deprecated alias for older scripts."""
	create_site_organization_units()


def create_hq_positions():
	for position_code, template, org_unit, parent, is_group, is_head in HQ_POSITIONS:
		if frappe.db.exists("Position", position_code):
			continue

		frappe.get_doc(
			{
				"doctype": "Position",
				"position_code": position_code,
				"position_template": template,
				"organization_unit": org_unit,
				"location_1": "Head Office",
				"site_organization_unit": HEAD_OFFICE_SITE,
				"parent_position": parent,
				"is_group": is_group,
				"is_head_position": is_head,
				"position_status": "Active",
			}
		).insert(ignore_permissions=True)


def create_sample_data():
	"""Create the full sample organization, location and position hierarchy."""
	create_roles()
	create_job_categories()
	create_job_grades()
	create_position_templates()
	create_branch_staffing_templates()
	create_regions()
	create_zones()
	create_cities()
	create_woredas()
	create_organization_units()
	create_site_organization_units()
	create_hq_positions()
	frappe.db.commit()
	print("Organization Structure sample data created successfully.")


def reset_sample_data():
	"""Delete ALL records in the module's doctypes for a clean reseed.

	    bench --site <site> execute hrms.organization_structure.setup.reset_sample_data

	WARNING: destructive. Removes every Position, Organization Unit,
	Position Template, Branch Staffing Template, Job Grade and Job Category
	(including manually created ones). Intended for development / demo environments.
	"""
	for assignment in frappe.get_all("Position Assignment", pluck="name"):
		frappe.delete_doc("Position Assignment", assignment, force=True)

	# Tree doctypes: delete descendants before ancestors (highest lft first).
	for position in frappe.get_all("Position", order_by="lft desc", pluck="name"):
		frappe.delete_doc("Position", position, force=True, ignore_on_trash=True)

	for woreda in frappe.get_all("Woreda", pluck="name"):
		frappe.delete_doc("Woreda", woreda, force=True)

	for city in frappe.get_all("City", pluck="name"):
		frappe.delete_doc("City", city, force=True)

	for zone in frappe.get_all("Zone", pluck="name"):
		frappe.delete_doc("Zone", zone, force=True)

	for region in frappe.get_all("Region", pluck="name"):
		frappe.delete_doc("Region", region, force=True)

	for unit in frappe.get_all("Organization Unit", order_by="lft desc", pluck="name"):
		frappe.delete_doc("Organization Unit", unit, force=True, ignore_on_trash=True)

	for template in frappe.get_all("Branch Staffing Template", pluck="name"):
		frappe.delete_doc("Branch Staffing Template", template, force=True)

	for template in frappe.get_all("Position Template", pluck="name"):
		frappe.delete_doc("Position Template", template, force=True)

	for grade in frappe.get_all("Job Grade", pluck="name"):
		frappe.delete_doc("Job Grade", grade, force=True)

	for category in frappe.get_all("Job Category", pluck="name"):
		frappe.delete_doc("Job Category", category, force=True)

	frappe.db.commit()
	print("Organization Structure data cleared.")


def verify_sample_data():
	"""Print a summary that exercises the controllers' computed fields.

	    bench --site <site> execute hrms.organization_structure.setup.verify_sample_data
	"""
	print("\n=== Masters ===")
	print(f"Job Grades:        {frappe.db.count('Job Grade')}")
	print(f"Position Templates: {frappe.db.count('Position Template')}")
	print(f"Staffing Plans:    {frappe.db.count('Branch Staffing Template')}")

	print("\n=== Geography Masters ===")
	print(f"Regions:  {frappe.db.count('Region')}")
	print(f"Zones:    {frappe.db.count('Zone')}")
	print(f"Cities:   {frappe.db.count('City')}")
	print(f"Woredas:  {frappe.db.count('Woreda')}")

	print("\n=== Physical Sites (organization units with Location 1) ===")
	sites = frappe.get_all(
		"Organization Unit",
		filters={"location_1": ["is", "set"]},
		fields=["unit_name", "location_1", "organization_level", "lft"],
		order_by="lft asc",
	)
	for site in sites:
		indent = "  " * max((site.organization_level or 1) - 1, 0)
		print(f"{indent}L{site.organization_level} {site.unit_name} ({site.location_1})")

	print("\n=== Positions per Branch (auto-generated, vacant) ===")
	for branch in frappe.get_all(
		"Organization Unit",
		filters={"location_1": "Branch"},
		fields=["name"],
		order_by="lft asc",
	):
		count = frappe.db.count("Position", {"site_organization_unit": branch.name})
		print(f"  {branch.name}: {count} positions")

	print("\n=== Head-office Positions (reporting tree) ===")
	positions = frappe.get_all(
		"Position",
		filters={"site_organization_unit": HEAD_OFFICE_SITE},
		fields=["position_code", "position_name", "position_level", "occupancy_status"],
		order_by="lft asc",
	)
	for pos in positions:
		indent = "  " * max((pos.position_level or 1) - 1, 0)
		print(f"{indent}L{pos.position_level} {pos.position_code} ({pos.occupancy_status})")

	print("\n=== Summary ===")
	print(f"Organization Units: {frappe.db.count('Organization Unit')}")
	print(f"Physical Sites:     {frappe.db.count('Organization Unit', {'location_1': ['is', 'set']})}")
	print(f"Positions:          {frappe.db.count('Position')}")
	print(f"Vacant Positions:   {frappe.db.count('Position', {'occupancy_status': 'Vacant'})}")
	print(f"Occupied Positions: {frappe.db.count('Position', {'occupancy_status': 'Occupied'})}")


def _import_fixture(relative_path: str):
	"""Import a JSON fixture bundled with this module (works with the Docker bind-mount)."""
	path = Path(__file__).resolve().parent / relative_path
	if not path.exists():
		return False

	import_file_by_path(str(path), force=True, ignore_version=True)
	return True


def patch_position_site_fields():
	"""Back-fill location_1 and site_organization_unit on positions from legacy fields."""
	location_name_map = {}
	if frappe.db.table_exists("tabLocation Unit"):
		location_name_map = {
			row.name: row
			for row in frappe.get_all(
				"Location Unit",
				fields=["name", "location_type"],
			)
		}

	if frappe.db.has_column("Position", "location_unit"):
		for row in frappe.get_all(
			"Position",
			filters={"location_unit": ["is", "set"]},
			fields=["name", "location_unit", "location_type", "location_1", "site_organization_unit"],
		):
			updates = {}
			site_name = row.location_unit
			if not frappe.db.exists("Organization Unit", site_name):
				legacy = location_name_map.get(site_name)
				if legacy and frappe.db.exists("Organization Unit", legacy.name):
					site_name = legacy.name

			if not row.site_organization_unit and site_name and frappe.db.exists(
				"Organization Unit", site_name
			):
				updates["site_organization_unit"] = site_name
			if not row.location_1:
				if row.location_type:
					updates["location_1"] = LOCATION_1_FROM_LEGACY.get(
						row.location_type, row.location_type
					)
				elif site_name and frappe.db.exists("Organization Unit", site_name):
					updates["location_1"] = frappe.db.get_value(
						"Organization Unit", site_name, "location_1"
					)
			if updates:
				frappe.db.set_value("Position", row.name, updates, update_modified=False)

	if frappe.db.has_column("Position", "location_type") and frappe.db.has_column(
		"Position", "location_1"
	):
		for row in frappe.get_all(
			"Position",
			filters={"location_type": ["is", "set"], "location_1": ["in", ("", None)]},
			fields=["name", "location_type"],
		):
			location_1 = LOCATION_1_FROM_LEGACY.get(row.location_type, row.location_type)
			if location_1:
				frappe.db.set_value("Position", row.name, "location_1", location_1, update_modified=False)


def migrate_location_units_to_organization_units():
	"""Copy legacy Location Unit records onto Organization Unit before dropping the doctype."""
	if not frappe.db.table_exists("tabLocation Unit"):
		return

	legacy_type_to_unit_type = {
		"Head Office": "Executive",
		"District": "District",
		"Branch": "Branch",
	}

	for loc in frappe.get_all(
		"Location Unit",
		fields=[
			"name",
			"location_name",
			"location_code",
			"location_type",
			"parent_location",
			"region",
			"zone",
			"city",
			"woreda",
			"address_line_1",
			"address_line_2",
			"postal_code",
			"phone",
			"email",
			"branch_staffing_template",
			"auto_create_positions",
			"status",
			"is_group",
		],
		order_by="lft asc",
	):
		location_1 = LOCATION_1_FROM_LEGACY.get(loc.location_type)
		if not location_1:
			continue

		if frappe.db.exists("Organization Unit", loc.name):
			frappe.db.set_value(
				"Organization Unit",
				loc.name,
				{
					"location_1": location_1,
					"unit_code": loc.location_code,
					"region": loc.region,
					"zone": loc.zone,
					"city": loc.city,
					"woreda": loc.woreda,
					"address_line_1": loc.address_line_1,
					"address_line_2": loc.address_line_2,
					"postal_code": loc.postal_code,
					"phone": loc.phone,
					"email": loc.email,
					"branch_staffing_template": loc.branch_staffing_template,
					"auto_create_positions": loc.auto_create_positions,
					"is_primary_head_office": 1 if location_1 == "Head Office" and not loc.parent_location else 0,
				},
				update_modified=False,
			)
			continue

		frappe.get_doc(
			{
				"doctype": "Organization Unit",
				"unit_name": loc.name,
				"unit_code": loc.location_code,
				"unit_type": legacy_type_to_unit_type.get(loc.location_type, "Other"),
				"parent_organization_unit": loc.parent_location,
				"is_group": loc.is_group,
				"status": loc.status or "Active",
				"location_1": location_1,
				"is_primary_head_office": 1 if location_1 == "Head Office" and not loc.parent_location else 0,
				"region": loc.region,
				"zone": loc.zone,
				"city": loc.city,
				"woreda": loc.woreda,
				"address_line_1": loc.address_line_1,
				"address_line_2": loc.address_line_2,
				"postal_code": loc.postal_code,
				"phone": loc.phone,
				"email": loc.email,
				"branch_staffing_template": loc.branch_staffing_template,
				"auto_create_positions": 0,
			}
		).insert(ignore_permissions=True)


def patch_position_location_types():
	"""Deprecated alias kept for older scripts."""
	patch_position_site_fields()


def patch_position_organization_units():
	"""Re-link positions to district/branch org units from cascade and location."""
	for name in frappe.get_all("Position", pluck="name"):
		doc = frappe.get_doc("Position", name)
		before = {
			"organization_unit": doc.organization_unit,
			"cost_center": doc.cost_center,
			"org_district": doc.org_district,
			"org_branch": doc.org_branch,
		}
		doc.sync_org_from_site()
		doc.set_organization_unit_from_cascade()
		updates = {
			field: doc.get(field)
			for field in before
			if doc.get(field) != before[field]
		}
		if updates:
			frappe.db.set_value("Position", name, updates, update_modified=False)


def refresh_module():
	"""Re-sync workspace, sidebar, and desktop icon, then clear cache.

	    bench --site <site> execute hrms.organization_structure.setup.refresh_module

	Use after editing workspace / sidebar JSON, or when the desk shows "not found".
	"""
	for fixture in (
		"fixtures/workspace.json",
		"workspace/organization_structure/organization_structure.json",
		"fixtures/workspace_sidebar.json",
		"fixtures/desktop_icon.json",
	):
		_import_fixture(fixture)

	migrate_location_units_to_organization_units()
	patch_position_site_fields()
	patch_position_organization_units()

	if not frappe.db.exists("Workspace", "Organization Structure"):
		frappe.throw(
			"Workspace 'Organization Structure' is still missing after import. "
			"Check that fixtures/workspace.json exists in the organization_structure module."
		)

	frappe.clear_cache()
	frappe.db.commit()
	print("Organization Structure refreshed. Log out and back in if the UI still looks stale.")


def fix_sidebar():
	"""Alias for :func:`refresh_module` (kept for older docs / scripts)."""
	refresh_module()


def diagnose():
	"""Check whether the workspace and its building blocks are registered.

	    bench --site <site> execute hrms.organization_structure.setup.diagnose
	"""
	print("\n=== Navigation ===")
	for doctype in ("Workspace Sidebar", "Desktop Icon"):
		name = "Organization Structure"
		print(f"{doctype}: {'OK' if frappe.db.exists(doctype, name) else 'MISSING'}")

	print("\n=== Workspace ===")
	ws = frappe.db.get_value(
		"Workspace",
		"Organization Structure",
		["name", "module", "public", "is_hidden"],
		as_dict=True,
	)
	print(ws or "MISSING: Workspace 'Organization Structure' not found")

	if ws:
		doc = frappe.get_doc("Workspace", "Organization Structure")
		print("Shortcuts:", [s.label for s in doc.shortcuts])

	print("\n=== Page ===")
	print(f"organization-chart: {'OK' if frappe.db.exists('Page', 'organization-chart') else 'MISSING'}")
	print(f"location-chart: {'OK' if frappe.db.exists('Page', 'location-chart') else 'MISSING'}")

	print("\n=== DocTypes ===")
	for dt in (
		"Organization Unit",
		"Region",
		"Zone",
		"City",
		"Woreda",
		"Position",
		"Position Template",
		"Job Grade",
		"Branch Staffing Template",
		"Branch Staffing Detail",
		"Job Category",
		"Position Assignment",
	):
		print(f"{dt}: {'OK' if frappe.db.exists('DocType', dt) else 'MISSING'}")

	print("\n=== Number Cards ===")
	for nc in (
		"Total Organization Units",
		"Total Locations",
		"Total Districts",
		"Total Branches",
		"Active Branches",
		"Inactive Branches",
		"Total Positions",
		"Occupied Positions",
		"Vacant Positions",
	):
		print(f"{nc}: {'OK' if frappe.db.exists('Number Card', nc) else 'MISSING'}")

	print("\n=== Reports ===")
	for rep in (
		"Organization Hierarchy",
		"Location Hierarchy",
		"Branch List",
		"District Summary",
		"Branches by Region",
		"Branches by Zone",
		"Branches by City",
		"Branches by Woreda",
		"Position Hierarchy",
		"Vacant Positions",
		"Positions by Organization Unit",
		"Positions by Location",
		"Span of Control",
		"Position Count by Function",
		"Job Category Distribution",
	):
		print(f"{rep}: {'OK' if frappe.db.exists('Report', rep) else 'MISSING'}")
