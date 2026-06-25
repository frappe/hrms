// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

// Organization Unit cascade: each level is filtered to children of the nearest parent above.
// Department/District share the same level; Team/Branch share the next level.
const ORG_CASCADE = [
	{
		field: "org_function",
		type: "Function",
		parentFields: [],
		clearDownstream: [
			"org_process",
			"org_sub_process",
			"org_department",
			"org_district",
			"org_team",
			"org_branch",
			"org_sub_team",
		],
	},
	{
		field: "org_process",
		type: "Process",
		parentFields: ["org_function"],
		clearDownstream: [
			"org_sub_process",
			"org_department",
			"org_district",
			"org_team",
			"org_branch",
			"org_sub_team",
		],
	},
	{
		field: "org_sub_process",
		type: "Sub-Process",
		parentFields: ["org_process", "org_function"],
		clearDownstream: [
			"org_department",
			"org_district",
			"org_team",
			"org_branch",
			"org_sub_team",
		],
	},
	{
		field: "org_department",
		type: "Department",
		parentFields: ["org_sub_process", "org_process", "org_function"],
		clearDownstream: ["org_team", "org_sub_team"],
	},
	{
		field: "org_district",
		type: "District",
		parentFields: ["org_sub_process", "org_process", "org_function"],
		clearDownstream: ["org_branch", "org_sub_team"],
	},
	{
		field: "org_team",
		type: "Team",
		parentFields: ["org_department", "org_sub_process", "org_process", "org_function"],
		clearDownstream: ["org_sub_team"],
	},
	{
		field: "org_branch",
		type: "Branch",
		parentFields: ["org_district", "org_sub_process", "org_process", "org_function"],
		clearDownstream: ["org_sub_team"],
	},
	{
		field: "org_sub_team",
		type: "Sub-Team",
		parentFields: [
			"org_team",
			"org_branch",
			"org_department",
			"org_district",
			"org_sub_process",
			"org_process",
			"org_function",
		],
		clearDownstream: [],
	},
];

function first_set_parent(frm, parentFields) {
	for (const field of parentFields) {
		if (frm.doc[field]) return frm.doc[field];
	}
	return null;
}

function set_org_cascade_queries(frm) {
	ORG_CASCADE.forEach((level) => {
		frm.set_query(level.field, () => {
			const filters = { unit_type: level.type };
			const parent = first_set_parent(frm, level.parentFields);
			if (parent) {
				filters.parent_organization_unit = parent;
			}
			return { filters };
		});
	});
}

function set_site_queries(frm) {
	frm.set_query("site_organization_unit", () => {
		const filters = { status: "Active", location_1: ["is", "set"] };
		if (frm.doc.location_1) {
			filters.location_1 = frm.doc.location_1;
		}
		return { filters };
	});
}

function sync_location_1_from_site(frm) {
	if (!frm.doc.site_organization_unit || frm.doc.location_1) return;

	frappe.db.get_value(
		"Organization Unit",
		frm.doc.site_organization_unit,
		"location_1",
		(r) => {
			if (r?.location_1) {
				frm.set_value("location_1", r.location_1);
			}
		},
	);
}

function clear_site_if_type_mismatch(frm) {
	if (!frm.doc.site_organization_unit || !frm.doc.location_1) return;

	frappe.db.get_value(
		"Organization Unit",
		frm.doc.site_organization_unit,
		"location_1",
		(r) => {
			if (r?.location_1 && r.location_1 !== frm.doc.location_1) {
				frm.set_value("site_organization_unit", null);
			}
		},
	);
}

function clear_downstream_org_levels(frm, changed_field) {
	const level = ORG_CASCADE.find((l) => l.field === changed_field);
	if (!level) return;

	level.clearDownstream.forEach((field) => {
		if (frm.doc[field]) {
			frm.set_value(field, null);
		}
	});
}

function resolve_organization_unit(frm) {
	sync_org_cascade_from_cost_center(frm);

	for (let i = ORG_CASCADE.length - 1; i >= 0; i--) {
		const value = frm.doc[ORG_CASCADE[i].field];
		if (value) {
			frm.set_value("organization_unit", value);
			frm.set_value("cost_center", value);
			return;
		}
	}

	if (frm.doc.cost_center) {
		frm.set_value("organization_unit", frm.doc.cost_center);
	} else {
		frm.set_value("organization_unit", null);
	}
}

function sync_org_cascade_from_cost_center(frm, unit_name) {
	const target = unit_name || frm.doc.cost_center;
	if (!target) return;

	frappe.db.get_value("Organization Unit", target, "unit_type", (r) => {
		if (!r?.unit_type) return;
		const field = {
			Function: "org_function",
			Process: "org_process",
			"Sub-Process": "org_sub_process",
			Department: "org_department",
			District: "org_district",
			Team: "org_team",
			Branch: "org_branch",
			"Sub-Team": "org_sub_team",
		}[r.unit_type];
		if (field && !frm.doc[field]) {
			frm.set_value(field, target);
		}
	});
}

function populate_org_cascade(frm) {
	if (!frm.doc.organization_unit) return;
	if (ORG_CASCADE.some((l) => frm.doc[l.field])) return;

	frappe.call({
		method: "hrms.organization_structure.doctype.position.position.get_organization_hierarchy",
		args: { organization_unit: frm.doc.organization_unit },
		callback: (r) => {
			if (!r.message) return;
			Object.entries(r.message).forEach(([field, value]) => {
				frm.doc[field] = value;
			});
			frm.refresh_fields(ORG_CASCADE.map((l) => l.field));
		},
	});
}

frappe.ui.form.on("Position", {
	onload(frm) {
		set_org_cascade_queries(frm);
		set_site_queries(frm);

		if (frm.is_new() && !frm.doc.company) {
			const company = frappe.defaults.get_user_default("Company");
			if (company) frm.set_value("company", company);
		}
	},

	refresh(frm) {
		frm.add_custom_button(__("Position Tree"), () => {
			frappe.set_route("Tree", "Position");
		});

		populate_org_cascade(frm);
		sync_location_1_from_site(frm);

		if (frm.doc.occupancy_status === "Occupied" && frm.doc.current_employee) {
			frm.dashboard.set_headline(
				__("Occupied by {0}", [frm.doc.current_employee.bold()]),
			);
		} else if (!frm.is_new()) {
			frm.dashboard.set_headline(__("This position is currently vacant."));
		}
	},

	position_template(frm) {
		if (!frm.doc.position_template) return;

		frappe.db.get_value(
			"Position Template",
			frm.doc.position_template,
			["job_grade", "job_category"],
			(r) => {
				if (!r) return;
				if (r.job_grade && !frm.doc.job_grade) {
					frm.set_value("job_grade", r.job_grade);
				}
				if (r.job_category && !frm.doc.job_category) {
					frm.set_value("job_category", r.job_category);
				}
			},
		);
	},

	location_1(frm) {
		clear_site_if_type_mismatch(frm);
	},

	site_organization_unit(frm) {
		if (frm.doc.site_organization_unit && !frm.doc.location_1) {
			frappe.db.get_value(
				"Organization Unit",
				frm.doc.site_organization_unit,
				"location_1",
				(r) => {
					if (r?.location_1) {
						frm.set_value("location_1", r.location_1);
					}
				},
			);
		}
	},

	org_function(frm) {
		clear_downstream_org_levels(frm, "org_function");
		resolve_organization_unit(frm);
	},

	org_process(frm) {
		clear_downstream_org_levels(frm, "org_process");
		resolve_organization_unit(frm);
	},

	org_sub_process(frm) {
		clear_downstream_org_levels(frm, "org_sub_process");
		resolve_organization_unit(frm);
	},

	org_department(frm) {
		clear_downstream_org_levels(frm, "org_department");
		resolve_organization_unit(frm);
	},

	org_district(frm) {
		clear_downstream_org_levels(frm, "org_district");
		resolve_organization_unit(frm);
	},

	org_team(frm) {
		clear_downstream_org_levels(frm, "org_team");
		resolve_organization_unit(frm);
	},

	org_branch(frm) {
		clear_downstream_org_levels(frm, "org_branch");
		resolve_organization_unit(frm);
	},

	org_sub_team(frm) {
		resolve_organization_unit(frm);
	},

	cost_center(frm) {
		sync_org_cascade_from_cost_center(frm);
		resolve_organization_unit(frm);
	},

	parent_position(frm) {
		if (frm.doc.parent_position === frm.doc.name) {
			frappe.msgprint(__("A Position cannot report to itself."));
			frm.set_value("parent_position", null);
		}
	},
});
