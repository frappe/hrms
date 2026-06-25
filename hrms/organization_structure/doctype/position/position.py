# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import re

import frappe
from frappe import _
from frappe.utils import cint
from frappe.utils.nestedset import NestedSet

from hrms.organization_structure.doctype.organization_unit.organization_unit import (
	update_descendant_levels,
	validate_circular_reference,
)

CODE_SUFFIX = re.compile(r"-(\d+)$")


class Position(NestedSet):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		company: DF.Link
		cost_center: DF.Link
		current_employee: DF.Link | None
		description: DF.SmallText | None
		incumbent_type: DF.Literal["Single", "Multiple"]
		is_group: DF.Check
		is_head_position: DF.Check
		is_occupied: DF.Check
		job_category: DF.Link
		job_grade: DF.Link
		lft: DF.Int
		location_1: DF.Literal["", "Head Office", "District Office", "Branch"]
		occupancy_status: DF.Literal["Vacant", "Occupied"]
		old_parent: DF.Link | None
		org_department: DF.Link | None
		org_district: DF.Link | None
		org_function: DF.Link | None
		org_process: DF.Link | None
		org_sub_process: DF.Link | None
		org_sub_team: DF.Link | None
		org_branch: DF.Link | None
		org_team: DF.Link | None
		organization_unit: DF.Link | None
		parent_position: DF.Link | None
		position_code: DF.Data | None
		position_critical: DF.Literal["Critical", "Not Critical"]
		position_level: DF.Int
		position_name: DF.Data
		position_start_date: DF.Date
		position_status: DF.Literal["Active", "Inactive"]
		position_template: DF.Link | None
		rgt: DF.Int
		site_organization_unit: DF.Link
	# end: auto-generated types

	nsm_parent_field = "parent_position"

	def autoname(self):
		# the position code is the document identity (e.g. TEL-BOL-001)
		self.apply_template_defaults()
		self.set_position_code()
		self.name = self.position_code

	def validate(self):
		validate_circular_reference(self)
		self.apply_template_defaults()
		self.set_position_code()
		self.set_position_name()
		self.set_position_level()
		self.sync_org_from_site()
		self.set_organization_unit_from_cascade()
		self.set_required_defaults()
		self.set_location_1_from_site()
		self.validate_site_placement()
		self.sync_occupancy_status()

	def on_update(self):
		NestedSet.on_update(self)
		self.update_descendant_levels()

	def on_trash(self):
		NestedSet.on_trash(self, allow_root_deletion=True)

	def apply_template_defaults(self):
		"""Inherit job grade and job category from the position template when not set."""
		if not self.position_template:
			return

		template = frappe.db.get_value(
			"Position Template",
			self.position_template,
			["job_grade", "job_category"],
			as_dict=True,
		)
		if not template:
			return

		if not self.job_grade:
			self.job_grade = template.job_grade
		if not self.job_category:
			self.job_category = template.job_category

	def sync_org_from_site(self):
		"""Link org district/branch cascade fields from the physical site when possible."""
		if not self.site_organization_unit:
			return

		site_location = frappe.db.get_value(
			"Organization Unit", self.site_organization_unit, ["location_1", "parent_organization_unit"],
			as_dict=True,
		)
		if not site_location or not site_location.location_1:
			return

		if site_location.location_1 == "Branch" and not self.org_branch:
			self.org_branch = self.site_organization_unit

		if site_location.location_1 == "Branch" and site_location.parent_organization_unit:
			parent_location = frappe.db.get_value(
				"Organization Unit", site_location.parent_organization_unit, "location_1"
			)
			if parent_location == "District Office" and not self.org_district:
				self.org_district = site_location.parent_organization_unit

		if site_location.location_1 == "District Office" and not self.org_district:
			self.org_district = self.site_organization_unit

	def sync_cascade_from_cost_center(self):
		"""Mirror cost centre into the matching cascade picker when that level is blank."""
		if not self.cost_center:
			return

		unit_type = frappe.db.get_value("Organization Unit", self.cost_center, "unit_type")
		field = ORG_CASCADE_FIELDS.get(unit_type)
		if field and not self.get(field):
			self.set(field, self.cost_center)

	def set_organization_unit_from_cascade(self):
		"""Resolve organization_unit to the deepest cascade picker (District beats Department, etc.)."""
		self.sync_cascade_from_cost_center()

		for field in reversed(ORG_CASCADE_FIELD_ORDER):
			value = self.get(field)
			if value:
				self.organization_unit = value
				if not self.cost_center or _should_prefer_organization_unit(value, self.cost_center):
					self.cost_center = value
				return

		if self.cost_center:
			self.organization_unit = self.cost_center

	def set_required_defaults(self):
		"""Fill mandatory fields that automated callers may leave blank.

		Mandatory validation runs after validate(), so populating the values here
		keeps both the form and the automated branch/HQ position generation working.
		"""
		if not self.company:
			self.company = default_company()
		if not self.cost_center:
			self.cost_center = self.organization_unit or default_organization_unit()
		elif self.organization_unit and _should_prefer_organization_unit(
			self.organization_unit, self.cost_center
		):
			self.cost_center = self.organization_unit

	def set_location_1_from_site(self):
		"""Back-fill location 1 from the linked site for legacy rows and automation."""
		if self.site_organization_unit and not self.location_1:
			self.location_1 = frappe.db.get_value(
				"Organization Unit", self.site_organization_unit, "location_1"
			)

	def validate_site_placement(self):
		if not self.location_1 or not self.site_organization_unit:
			return

		site_location = frappe.db.get_value(
			"Organization Unit", self.site_organization_unit, "location_1"
		)
		if site_location and site_location != self.location_1:
			frappe.throw(
				_("Site {0} has Location 1 = {1}, not {2}.").format(
					frappe.bold(self.site_organization_unit),
					frappe.bold(site_location),
					frappe.bold(self.location_1),
				)
			)

	def set_position_code(self):
		if self.position_code:
			return

		prefix = self._code_prefix()
		self.position_code = f"{prefix}-{self._next_sequence(prefix):03d}"

	def _code_prefix(self) -> str:
		"""Build the <TEMPLATE>-<LOCATION/ORG> stem for a generated position code."""
		template_code = (
			frappe.db.get_value("Position Template", self.position_template, "template_code")
			if self.position_template
			else None
		)
		place_code = None
		if self.site_organization_unit:
			place_code = frappe.db.get_value(
				"Organization Unit", self.site_organization_unit, "unit_code"
			)
		elif self.organization_unit:
			place_code = frappe.db.get_value("Organization Unit", self.organization_unit, "unit_code")

		parts = [template_code or "POS"]
		if place_code:
			parts.append(place_code)
		return "-".join(part for part in parts if part)

	def _next_sequence(self, prefix: str) -> int:
		"""Return the next running number for codes sharing this prefix."""
		existing = frappe.get_all(
			"Position",
			filters={"position_code": ["like", f"{prefix}-%"], "name": ["!=", self.name or ""]},
			pluck="position_code",
		)
		highest = 0
		for code in existing:
			match = CODE_SUFFIX.search(code or "")
			if match:
				highest = max(highest, int(match.group(1)))
		return highest + 1

	def set_position_name(self):
		if self.position_name:
			return

		if self.position_template:
			template_name = frappe.db.get_value(
				"Position Template", self.position_template, "template_name"
			)
			self.position_name = f"{template_name} - {self.position_code}"
		else:
			self.position_name = self.position_code

	def set_position_level(self):
		if self.parent_position:
			parent_level = frappe.db.get_value("Position", self.parent_position, "position_level")
			self.position_level = cint(parent_level) + 1
		else:
			self.position_level = 1

	def update_descendant_levels(self):
		doc_before_save = self.get_doc_before_save()
		if doc_before_save and doc_before_save.position_level == self.position_level:
			return

		update_descendant_levels(self, "position_level")

	def sync_occupancy_status(self):
		self.occupancy_status = "Occupied" if self.is_occupied else "Vacant"


# Ordered cascade fields on the Position form (shallow -> deep).
ORG_CASCADE_FIELD_ORDER = [
	"org_function",
	"org_process",
	"org_sub_process",
	"org_department",
	"org_district",
	"org_team",
	"org_branch",
	"org_sub_team",
]

# Maps the Position cascade fields to the Organization Unit type they select.
ORG_CASCADE_FIELDS = {
	"Function": "org_function",
	"Process": "org_process",
	"Sub-Process": "org_sub_process",
	"Department": "org_department",
	"District": "org_district",
	"Team": "org_team",
	"Branch": "org_branch",
	"Sub-Team": "org_sub_team",
}


def find_org_unit_by_location_name(location_name: str, unit_type: str) -> str | None:
	"""Match an organization unit to a location by name and type."""
	if not location_name or not unit_type:
		return None

	exact = frappe.db.get_value(
		"Organization Unit",
		{"unit_name": location_name, "unit_type": unit_type},
		"name",
	)
	if exact:
		return exact

	# tolerate minor spelling differences (e.g. Branch vs Brancch)
	candidates = frappe.get_all(
		"Organization Unit",
		filters={"unit_type": unit_type},
		fields=["name", "unit_name"],
	)
	location_key = location_name.lower().replace(" ", "")
	for row in candidates:
		candidate_key = (row.unit_name or "").lower().replace(" ", "")
		if location_key[:5] and candidate_key.startswith(location_key[:5]):
			return row.name
		if location_key and location_key in candidate_key:
			return row.name

	return None


def resolve_position_chart_unit(row) -> str | None:
	"""Pick the org unit box a position belongs to on the organization chart."""
	for field in ("org_branch", "org_district", "organization_unit"):
		value = row.get(field) if isinstance(row, dict) else getattr(row, field, None)
		if value:
			return value

	site = row.get("site_organization_unit") if isinstance(row, dict) else getattr(
		row, "site_organization_unit", None
	)
	if site:
		site_location = frappe.db.get_value("Organization Unit", site, "location_1")
		if site_location == "Branch":
			return site
		if site_location == "District Office":
			return site

	return None


def _legacy_resolve_org_units_from_location(location_unit: str) -> dict[str, str]:
	"""Migration helper when Location Unit still exists on old databases."""
	if not frappe.db.exists("DocType", "Location Unit"):
		return {}

	loc = frappe.db.get_value(
		"Location Unit",
		location_unit,
		["location_name", "location_type", "parent_location"],
		as_dict=True,
	)
	if not loc or not loc.location_type:
		return {}

	location_1_map = {"Head Office": "Head Office", "District": "District Office", "Branch": "Branch"}
	loc_type = location_1_map.get(loc.location_type)
	result: dict[str, str] = {}

	if loc_type == "Branch":
		branch = find_org_unit_by_location_name(loc.location_name, "Branch")
		if branch:
			result["org_branch"] = branch
		if loc.parent_location:
			district_name = frappe.db.get_value("Location Unit", loc.parent_location, "location_name")
			district = find_org_unit_by_location_name(district_name, "District")
			if district:
				result["org_district"] = district
	elif loc_type == "District Office":
		district = find_org_unit_by_location_name(loc.location_name, "District")
		if district:
			result["org_district"] = district

	return result


def get_deepest_organization_unit(units: list[str]) -> str | None:
	"""Pick the deepest unit by cascade field order (used when only names are available)."""
	if not units:
		return None

	field_order = {field: index for index, field in enumerate(ORG_CASCADE_FIELD_ORDER)}
	rows = frappe.get_all(
		"Organization Unit",
		filters={"name": ["in", list(set(units))]},
		fields=["name", "unit_type"],
	)
	if not rows:
		return None

	return max(
		rows,
		key=lambda row: field_order.get(ORG_CASCADE_FIELDS.get(row.unit_type), -1),
	).name


def _should_prefer_organization_unit(unit_a: str, unit_b: str) -> bool:
	"""True when unit_a is deeper than or equal to unit_b in the cascade."""
	field_order = {field: index for index, field in enumerate(ORG_CASCADE_FIELD_ORDER)}

	def depth(unit: str) -> int:
		unit_type = frappe.db.get_value("Organization Unit", unit, "unit_type")
		return field_order.get(ORG_CASCADE_FIELDS.get(unit_type), -1)

	return depth(unit_a) >= depth(unit_b)


def _is_deeper_organization_unit(unit_a: str, unit_b: str) -> bool:
	return _should_prefer_organization_unit(unit_a, unit_b) and unit_a != unit_b


@frappe.whitelist()
def get_deepest_organization_unit_api(organization_units: list[str] | str) -> str | None:
	if isinstance(organization_units, str):
		import json

		organization_units = json.loads(organization_units)
	return get_deepest_organization_unit(organization_units)


@frappe.whitelist()
def get_organization_hierarchy(organization_unit: str) -> dict:
	"""Return the cascade field values for a unit by walking its ancestors by type.

	Used by the form to rebuild the Function -> ... -> Sub-Team selectors when an
	existing position (which only stores the resolved organization_unit) is opened.
	"""
	from frappe.utils.nestedset import get_ancestors_of

	if not organization_unit or not frappe.db.exists("Organization Unit", organization_unit):
		return {}

	chain = [organization_unit, *get_ancestors_of("Organization Unit", organization_unit)]
	types = frappe.get_all(
		"Organization Unit",
		filters={"name": ["in", chain]},
		fields=["name", "unit_type"],
	)

	result = {}
	for unit in types:
		field = ORG_CASCADE_FIELDS.get(unit.unit_type)
		if field:
			result[field] = unit.name

	# the resolved unit must win for its own type (e.g. District, not an ancestor Sub-Process)
	resolved_type = frappe.db.get_value("Organization Unit", organization_unit, "unit_type")
	resolved_field = ORG_CASCADE_FIELDS.get(resolved_type)
	if resolved_field:
		result[resolved_field] = organization_unit

	return result


def default_company() -> str | None:
	"""Resolve a sensible default company for positions created without one."""
	company = frappe.defaults.get_global_default("company") or frappe.defaults.get_user_default(
		"company"
	)
	if company:
		return company

	companies = frappe.get_all("Company", pluck="name", limit=1)
	return companies[0] if companies else None


def default_organization_unit() -> str | None:
	"""Topmost organization unit, used as a fallback cost centre."""
	roots = frappe.get_all(
		"Organization Unit",
		filters={"parent_organization_unit": ["in", ("", None)]},
		pluck="name",
		limit=1,
	)
	if roots:
		return roots[0]

	units = frappe.get_all("Organization Unit", pluck="name", limit=1)
	return units[0] if units else None


def update_occupancy(position: str):
	"""Refresh the occupancy snapshot of a Position based on its active assignments."""
	if not position or not frappe.db.exists("Position", position):
		return

	active_employee = frappe.db.get_value(
		"Position Assignment",
		{"position": position, "status": "Active"},
		"employee",
		order_by="start_date desc",
	)

	frappe.db.set_value(
		"Position",
		position,
		{
			"is_occupied": 1 if active_employee else 0,
			"occupancy_status": "Occupied" if active_employee else "Vacant",
			"current_employee": active_employee or None,
		},
		update_modified=False,
	)


@frappe.whitelist()
def get_children(doctype: str, parent: str = "", is_root: bool = False, **filters) -> list[dict]:
	Position = frappe.qb.DocType("Position")

	query = frappe.qb.from_(Position).select(
		Position.name.as_("value"),
		Position.position_name.as_("title"),
		Position.is_group.as_("expandable"),
		Position.organization_unit,
		Position.location_1,
		Position.site_organization_unit,
		Position.job_grade,
		Position.position_status,
		Position.occupancy_status,
		Position.is_occupied,
		Position.current_employee,
		Position.is_head_position,
	)

	for field in ("organization_unit", "location_1", "site_organization_unit", "job_grade", "position_status"):
		if filters.get(field):
			query = query.where(Position[field] == filters.get(field))

	if parent and not cint(is_root):
		query = query.where(Position.parent_position == parent)
	else:
		query = query.where((Position.parent_position == "") | (Position.parent_position.isnull()))

	return query.orderby(Position.position_name).run(as_dict=True)


@frappe.whitelist()
def add_tree_node():
	from frappe.desk.treeview import make_tree_args

	args = make_tree_args(**frappe.form_dict)

	if args.parent_position == "All Positions" or not frappe.db.exists("Position", args.parent_position):
		args.parent_position = None
	else:
		# a node that gets children must be a group
		frappe.db.set_value("Position", args.parent_position, "is_group", 1)

	frappe.get_doc(args).insert()
