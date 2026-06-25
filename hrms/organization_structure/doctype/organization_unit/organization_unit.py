# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import re

import frappe
from frappe import _
from frappe.utils import cint
from frappe.utils.nestedset import NestedSet

REQUIRED_PARENT_LOCATION_1 = {
	"District Office": "Head Office",
	"Branch": "District Office",
}

LOCATION_1_ORDER = {"Head Office": 0, "District Office": 1, "Branch": 2}

GEO_FIELDS = ("region", "zone", "city", "woreda", "address_line_1", "address_line_2", "postal_code", "phone", "email")

# Unit types whose code is just their own short code (the CEO/Executive root is
# implicit and never prefixed onto a Function code) — see spec §4.1.
TOP_LEVEL_UNIT_TYPES = {"Executive", "Function"}

# Unit types that embed their type code into the hierarchy path (spec §4.4–4.8).
# Function / Process / Sub-Process intentionally omit it.
UNIT_TYPE_PATH_PREFIX = {
	"Department": "DEP",
	"District": "DST",
	"Branch": "BRN",
	"Team": "TEM",
	"Sub-Team": "STM",
}

# Connector words dropped when abbreviating a multi-word unit name (spec §6.3).
SHORT_CODE_IGNORE_WORDS = {"and", "of", "the", "for", "to", "in", "on", "at", "by", "with"}


class OrganizationUnit(NestedSet):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		address_line_1: DF.Data | None
		address_line_2: DF.Data | None
		auto_create_positions: DF.Check
		branch_staffing_template: DF.Link | None
		city: DF.Link | None
		description: DF.SmallText | None
		email: DF.Data | None
		inherit_ho_geography: DF.Check
		is_group: DF.Check
		is_primary_head_office: DF.Check
		lft: DF.Int
		location_1: DF.Literal["", "Head Office", "District Office", "Branch"]
		old_parent: DF.Link | None
		organization_level: DF.Int
		parent_organization_unit: DF.Link | None
		phone: DF.Data | None
		postal_code: DF.Data | None
		region: DF.Link | None
		rgt: DF.Int
		short_code: DF.Data | None
		status: DF.Literal["Active", "Inactive"]
		unit_code: DF.Data | None
		unit_name: DF.Data
		unit_type: DF.Literal["", "Executive", "Function", "Process", "Sub-Process", "Department", "District", "Team", "Branch", "Sub-Team", "Other"]
		woreda: DF.Link | None
		zone: DF.Link | None
	# end: auto-generated types

	nsm_parent_field = "parent_organization_unit"

	def validate(self):
		validate_circular_reference(self)
		self.set_short_code()
		self.set_unit_code()
		self.set_ho_inheritance_flags()
		self.apply_inherited_ho_geography()
		self.validate_location_hierarchy()
		self.validate_geography()
		self.validate_primary_head_office()
		self.validate_staffing_template()
		self.set_organization_level()
		self.set_group_flag()

	def on_update(self):
		NestedSet.on_update(self)
		self.update_descendant_levels()
		self.propagate_ho_geography_if_primary()

	def on_trash(self):
		NestedSet.on_trash(self, allow_root_deletion=True)

	def after_insert(self):
		self.auto_generate_branch_positions()

	def set_ho_inheritance_flags(self):
		if self.location_1 == "Head Office" and not self.is_primary_head_office:
			self.inherit_ho_geography = 1
		elif self.location_1 != "Head Office":
			self.inherit_ho_geography = 0
			self.is_primary_head_office = 0

	def apply_inherited_ho_geography(self):
		if self.location_1 != "Head Office" or self.is_primary_head_office or not self.inherit_ho_geography:
			return

		primary = get_primary_head_office()
		if not primary or primary == self.name:
			return

		geo = frappe.db.get_value("Organization Unit", primary, list(GEO_FIELDS), as_dict=True)
		if not geo:
			return

		for field in GEO_FIELDS:
			self.set(field, geo.get(field))

	def validate_location_hierarchy(self):
		if not self.location_1:
			return

		if self.location_1 == "Head Office":
			return

		expected_parent_location = REQUIRED_PARENT_LOCATION_1.get(self.location_1)
		if not expected_parent_location:
			return

		if not self.parent_organization_unit:
			frappe.throw(
				_("Parent Organization Unit is required for {0}.").format(frappe.bold(self.location_1))
			)

		parent_location = frappe.db.get_value(
			"Organization Unit", self.parent_organization_unit, "location_1"
		)
		if parent_location != expected_parent_location:
			frappe.throw(
				_("{0} must report to a {1}, not a {2}.").format(
					frappe.bold(self.location_1),
					frappe.bold(expected_parent_location),
					frappe.bold(parent_location or _("unit without a site type")),
				)
			)

	def validate_geography(self):
		if self.region and frappe.db.get_value("Region", self.region, "status") == "Inactive":
			frappe.throw(_("Region {0} is inactive.").format(frappe.bold(self.region)))

		if self.zone:
			zone = frappe.db.get_value("Zone", self.zone, ["region", "status"], as_dict=True)
			if zone and zone.status == "Inactive":
				frappe.throw(_("Zone {0} is inactive.").format(frappe.bold(self.zone)))
			if self.region and zone and zone.region != self.region:
				frappe.throw(
					_("Zone {0} does not belong to Region {1}.").format(
						frappe.bold(self.zone), frappe.bold(self.region)
					)
				)

		if self.city:
			city = frappe.db.get_value("City", self.city, ["region", "zone", "status"], as_dict=True)
			if city and city.status == "Inactive":
				frappe.throw(_("City {0} is inactive.").format(frappe.bold(self.city)))
			if self.region and city and city.region != self.region:
				frappe.throw(
					_("City {0} does not belong to Region {1}.").format(
						frappe.bold(self.city), frappe.bold(self.region)
					)
				)
			if self.zone and city and city.zone != self.zone:
				frappe.throw(
					_("City {0} does not belong to Zone {1}.").format(
						frappe.bold(self.city), frappe.bold(self.zone)
					)
				)

		if self.woreda:
			woreda_city = frappe.db.get_value("Woreda", self.woreda, ["city", "status"], as_dict=True)
			if woreda_city and woreda_city.status == "Inactive":
				frappe.throw(_("Woreda {0} is inactive.").format(frappe.bold(self.woreda)))
			if self.city and woreda_city and woreda_city.city != self.city:
				frappe.throw(
					_("Woreda {0} does not belong to City {1}.").format(
						frappe.bold(self.woreda), frappe.bold(self.city)
					)
				)

	def validate_primary_head_office(self):
		if not self.is_primary_head_office:
			return

		existing = frappe.db.get_value(
			"Organization Unit",
			{
				"is_primary_head_office": 1,
				"name": ["!=", self.name or ""],
			},
			"name",
		)
		if existing:
			frappe.throw(
				_("Primary Head Office is already set on {0}.").format(frappe.bold(existing))
			)

	def validate_staffing_template(self):
		if self.branch_staffing_template and self.location_1 != "Branch":
			frappe.throw(
				_("A Branch Staffing Template can only be set on a unit with Location 1 = {0}.").format(
					frappe.bold("Branch")
				)
			)

	def set_short_code(self):
		"""Use the manual short code when given (cleaned), else abbreviate the unit name."""
		if self.short_code:
			self.short_code = clean_short_code(self.short_code)
		else:
			self.short_code = generate_short_code(self.unit_name)

	def set_unit_code(self):
		"""Generate the hierarchy-based unit code once, on creation.

		A code that already exists is left untouched so that renaming or moving a
		unit never silently rewrites a code that positions / reports depend on
		(spec §11). Regeneration after a move is a deliberate, separate action.
		"""
		if self.unit_code:
			return

		parent_code = None
		if self.parent_organization_unit:
			parent_code = frappe.db.get_value(
				"Organization Unit", self.parent_organization_unit, "unit_code"
			)

		proposed = build_unit_code(self.unit_type, parent_code, self.short_code)
		if not proposed:
			return

		self.unit_code = make_unique_unit_code(proposed, self.name)

	def set_organization_level(self):
		if self.parent_organization_unit:
			parent_level = frappe.db.get_value(
				"Organization Unit", self.parent_organization_unit, "organization_level"
			)
			self.organization_level = cint(parent_level) + 1
		else:
			self.organization_level = 1

	def set_group_flag(self):
		if self.location_1 in ("Head Office", "District Office"):
			self.is_group = 1

	def update_descendant_levels(self):
		doc_before_save = self.get_doc_before_save()
		if doc_before_save and doc_before_save.organization_level == self.organization_level:
			return

		update_descendant_levels(self, "organization_level")

	def propagate_ho_geography_if_primary(self):
		if not self.is_primary_head_office or self.location_1 != "Head Office":
			return

		if not any(self.get(field) for field in GEO_FIELDS):
			return

		updates = {field: self.get(field) for field in GEO_FIELDS}
		for unit in frappe.get_all(
			"Organization Unit",
			filters={
				"location_1": "Head Office",
				"inherit_ho_geography": 1,
				"name": ["!=", self.name],
			},
			pluck="name",
		):
			frappe.db.set_value("Organization Unit", unit, updates, update_modified=False)

	def auto_generate_branch_positions(self):
		if self.location_1 != "Branch":
			return
		if not (self.branch_staffing_template and self.auto_create_positions):
			return

		created = generate_positions_for_branch(self.name)
		if created:
			frappe.msgprint(
				_("Created {0} vacant position(s) for branch {1}.").format(
					len(created), frappe.bold(self.unit_name)
				),
				alert=True,
			)


def get_primary_head_office() -> str | None:
	primary = frappe.db.get_value(
		"Organization Unit",
		{"is_primary_head_office": 1, "location_1": "Head Office"},
		"name",
	)
	if primary:
		return primary

	return frappe.db.get_value(
		"Organization Unit",
		{"location_1": "Head Office"},
		"name",
		order_by="lft asc",
	)


def clean_short_code(value: str | None) -> str:
	"""Uppercase and strip everything but letters and digits (spec §6.4)."""
	return re.sub(r"[^A-Za-z0-9]", "", value or "").upper()


def generate_short_code(unit_name: str | None) -> str:
	"""Abbreviate a unit name per spec §6.

	Multi-word names use the first letter of each meaningful word (connector words
	dropped); single-word names use the first three letters. Always uppercase and
	alphanumeric.
	"""
	words = re.sub(r"[^A-Za-z0-9]", " ", unit_name or "").split()
	meaningful = [word for word in words if word.lower() not in SHORT_CODE_IGNORE_WORDS]
	# fall back to all words if the name is made up entirely of connector words
	meaningful = meaningful or words
	if not meaningful:
		return ""

	if len(meaningful) == 1:
		code = meaningful[0][:3]
	else:
		code = "".join(word[0] for word in meaningful)
	return code.upper()


def build_unit_code(unit_type: str | None, parent_code: str | None, short_code: str | None) -> str:
	"""Compose the hierarchy-based unit code from the parent code and unit type (spec §4)."""
	short_code = short_code or ""
	if not short_code:
		return ""

	# Function (and the implicit Executive/CEO root) carry only their own short code.
	if unit_type in TOP_LEVEL_UNIT_TYPES or not parent_code:
		return short_code

	type_prefix = UNIT_TYPE_PATH_PREFIX.get(unit_type)
	if type_prefix:
		return f"{parent_code}-{type_prefix}-{short_code}"
	return f"{parent_code}-{short_code}"


def _unit_code_taken(unit_code: str, exclude_name: str | None) -> bool:
	return bool(
		frappe.db.get_value(
			"Organization Unit",
			{"unit_code": unit_code, "name": ["!=", exclude_name or ""]},
			"name",
		)
	)


def make_unique_unit_code(proposed: str, exclude_name: str | None = None) -> str:
	"""Return the proposed code, appending -02, -03 … if it is already taken (spec §7)."""
	if not _unit_code_taken(proposed, exclude_name):
		return proposed

	sequence = 2
	while _unit_code_taken(f"{proposed}-{sequence:02d}", exclude_name):
		sequence += 1
	return f"{proposed}-{sequence:02d}"


@frappe.whitelist()
def preview_unit_code(
	unit_type: str | None = None,
	parent_organization_unit: str | None = None,
	unit_name: str | None = None,
	short_code: str | None = None,
) -> dict:
	"""Compute the short code and unit code for the live form preview (no write, no sequencing)."""
	resolved_short_code = clean_short_code(short_code) if short_code else generate_short_code(unit_name)
	parent_code = None
	if parent_organization_unit:
		parent_code = frappe.db.get_value("Organization Unit", parent_organization_unit, "unit_code")

	proposed = build_unit_code(unit_type, parent_code, resolved_short_code)
	return {
		"short_code": resolved_short_code,
		# show the same value that will be saved, including any -02 sequence suffix
		"unit_code": make_unique_unit_code(proposed) if proposed else "",
	}


def generate_positions_for_branch(organization_unit: str) -> list[str]:
	"""Create vacant positions defined by a branch unit's staffing template."""
	branch = frappe.db.get_value(
		"Organization Unit",
		organization_unit,
		["name", "unit_name", "location_1", "branch_staffing_template"],
		as_dict=True,
	)
	if not branch or branch.location_1 != "Branch" or not branch.branch_staffing_template:
		return []

	staffing = frappe.get_doc("Branch Staffing Template", branch.branch_staffing_template)
	created = []

	for row in staffing.staffing_details:
		existing = frappe.db.count(
			"Position",
			{"position_template": row.position_template, "site_organization_unit": branch.name},
		)
		for _seat in range(existing, cint(row.quantity)):
			position = frappe.get_doc(
				{
					"doctype": "Position",
					"position_template": row.position_template,
					"location_1": "Branch",
					"site_organization_unit": branch.name,
					"position_status": "Active",
					"occupancy_status": "Vacant",
				}
			).insert(ignore_permissions=True)
			created.append(position.name)

	return created


@frappe.whitelist()
def create_branch_positions(organization_unit: str) -> dict:
	created = generate_positions_for_branch(organization_unit)
	frappe.db.commit()
	return {"created": created, "count": len(created)}


@frappe.whitelist()
def propagate_ho_geography(organization_unit: str) -> dict:
	"""Apply primary Head Office geography to all inheriting Head Office units."""
	primary = frappe.get_doc("Organization Unit", organization_unit)
	if not primary.is_primary_head_office:
		frappe.throw(_("Only the primary Head Office can propagate geography."))

	updates = {field: primary.get(field) for field in GEO_FIELDS}
	count = 0
	for unit in frappe.get_all(
		"Organization Unit",
		filters={
			"location_1": "Head Office",
			"inherit_ho_geography": 1,
			"name": ["!=", primary.name],
		},
		pluck="name",
	):
		frappe.db.set_value("Organization Unit", unit, updates, update_modified=False)
		count += 1

	frappe.db.commit()
	return {"updated": count}


@frappe.whitelist()
def get_children(doctype: str, parent: str = "", is_root: bool = False, **filters) -> list[dict]:
	OrganizationUnit = frappe.qb.DocType("Organization Unit")

	query = frappe.qb.from_(OrganizationUnit).select(
		OrganizationUnit.name.as_("value"),
		OrganizationUnit.unit_name.as_("title"),
		OrganizationUnit.is_group.as_("expandable"),
		OrganizationUnit.unit_type,
		OrganizationUnit.location_1,
		OrganizationUnit.status,
	)

	if filters.get("unit_type"):
		query = query.where(OrganizationUnit.unit_type == filters.get("unit_type"))

	if filters.get("location_1"):
		query = query.where(OrganizationUnit.location_1 == filters.get("location_1"))

	if filters.get("status"):
		query = query.where(OrganizationUnit.status == filters.get("status"))

	if parent and not cint(is_root):
		query = query.where(OrganizationUnit.parent_organization_unit == parent)
	else:
		query = query.where(
			(OrganizationUnit.parent_organization_unit == "")
			| (OrganizationUnit.parent_organization_unit.isnull())
		)

	return query.orderby(OrganizationUnit.unit_name).run(as_dict=True)


@frappe.whitelist()
def add_tree_node():
	from frappe.desk.treeview import make_tree_args

	args = make_tree_args(**frappe.form_dict)

	if args.parent_organization_unit == "All Organization Units" or not frappe.db.exists(
		"Organization Unit", args.parent_organization_unit
	):
		args.parent_organization_unit = None
	else:
		frappe.db.set_value("Organization Unit", args.parent_organization_unit, "is_group", 1)

	frappe.get_doc(args).insert()


def validate_circular_reference(doc):
	"""Prevent a node from being placed under itself or one of its own descendants."""
	parent = doc.get(doc.nsm_parent_field)
	if not parent:
		return

	if parent == doc.name:
		frappe.throw(_("{0} cannot be its own parent.").format(_(doc.doctype)), title=_("Invalid Hierarchy"))

	ancestor = parent
	visited = set()
	while ancestor:
		if ancestor == doc.name:
			frappe.throw(
				_("Circular reference detected: {0} cannot report to one of its own descendants.").format(
					frappe.bold(doc.name)
				),
				title=_("Invalid Hierarchy"),
			)
		if ancestor in visited:
			break
		visited.add(ancestor)
		ancestor = frappe.db.get_value(doc.doctype, ancestor, doc.nsm_parent_field)


def update_descendant_levels(doc, level_field):
	descendants = frappe.get_all(
		doc.doctype,
		filters={"lft": [">", doc.lft], "rgt": ["<", doc.rgt]},
		fields=["name", doc.nsm_parent_field],
		order_by="lft asc",
	)

	level_map = {doc.name: cint(doc.get(level_field))}
	for node in descendants:
		parent = node.get(doc.nsm_parent_field)
		level = level_map.get(parent, cint(doc.get(level_field))) + 1
		level_map[node.name] = level
		frappe.db.set_value(doc.doctype, node.name, level_field, level, update_modified=False)
