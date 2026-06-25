// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

const PARENT_LOCATION_1 = {
	"District Office": "Head Office",
	Branch: "District Office",
};

frappe.ui.form.on("Organization Unit", {
	setup(frm) {
		frm.set_query("region", () => ({
			filters: { status: "Active" },
		}));

		frm.set_query("zone", () => {
			const filters = { status: "Active" };
			if (frm.doc.region) filters.region = frm.doc.region;
			return { filters };
		});

		frm.set_query("city", () => {
			const filters = { status: "Active" };
			if (frm.doc.region) filters.region = frm.doc.region;
			if (frm.doc.zone) filters.zone = frm.doc.zone;
			return { filters };
		});

		frm.set_query("woreda", () => {
			const filters = { status: "Active" };
			if (frm.doc.city) filters.city = frm.doc.city;
			return { filters };
		});

		frm.set_query("parent_organization_unit", () => {
			if (!frm.doc.location_1 || frm.doc.location_1 === "Head Office") {
				return {};
			}
			const expected = PARENT_LOCATION_1[frm.doc.location_1];
			if (!expected) return {};
			return {
				filters: {
					location_1: expected,
					status: "Active",
				},
			};
		});
	},

	refresh(frm) {
		frm.add_custom_button(__("Organization Tree"), () => {
			frappe.set_route("Tree", "Organization Unit");
		});

		if (!frm.is_new()) {
			frm.add_custom_button(__("Location Chart"), () => {
				frappe.set_route("location-chart");
			});

			frm.add_custom_button(
				__("Positions"),
				() => {
					frappe.set_route("List", "Position", {
						site_organization_unit: frm.doc.name,
					});
				},
				__("View"),
			);
		}

		if (frm.doc.location_1 === "Branch" && !frm.is_new()) {
			frm.add_custom_button(
				__("Generate Positions"),
				() => generate_branch_positions(frm),
				__("Actions"),
			);
		}

		if (frm.doc.is_primary_head_office && !frm.is_new()) {
			frm.add_custom_button(
				__("Apply Geography to Head Offices"),
				() => propagate_ho_geography(frm),
				__("Actions"),
			);
		}
	},

	location_1(frm) {
		if (frm.doc.location_1 === "Head Office") {
			if (!frm.doc.is_primary_head_office) {
				frm.set_value("inherit_ho_geography", 1);
			}
		} else {
			frm.set_value("is_primary_head_office", 0);
			frm.set_value("inherit_ho_geography", 0);
		}

		if (frm.doc.parent_organization_unit) {
			const expected = PARENT_LOCATION_1[frm.doc.location_1];
			if (expected) {
				frappe.db.get_value(
					"Organization Unit",
					frm.doc.parent_organization_unit,
					"location_1",
					(r) => {
						if (r && r.location_1 !== expected) {
							frm.set_value("parent_organization_unit", null);
						}
					},
				);
			}
		}
	},

	is_primary_head_office(frm) {
		if (frm.doc.is_primary_head_office) {
			frm.set_value("inherit_ho_geography", 0);
		} else if (frm.doc.location_1 === "Head Office") {
			frm.set_value("inherit_ho_geography", 1);
		}
	},

	region(frm) {
		clear_dependent_geo(frm, "region");
	},

	zone(frm) {
		clear_dependent_geo(frm, "zone");
	},

	city(frm) {
		if (frm.doc.woreda) {
			frappe.db.get_value("Woreda", frm.doc.woreda, "city", (r) => {
				if (r && r.city !== frm.doc.city) frm.set_value("woreda", null);
			});
		}
	},

	parent_organization_unit(frm) {
		if (frm.doc.parent_organization_unit === frm.doc.name) {
			frappe.msgprint(__("An Organization Unit cannot be its own parent."));
			frm.set_value("parent_organization_unit", null);
		}
		update_unit_code_preview(frm);
	},

	unit_name(frm) {
		update_unit_code_preview(frm);
	},

	unit_type(frm) {
		update_unit_code_preview(frm);
	},

	short_code(frm) {
		update_unit_code_preview(frm);
	},
});

function update_unit_code_preview(frm) {
	// Fill the read-only Unit Code field live as the user builds a new unit, so
	// the generated code is visible before saving. Existing units keep their code,
	// so no preview runs on edit.
	if (!frm.is_new()) return;
	if (!frm.doc.unit_name && !frm.doc.short_code) {
		frm.set_value("unit_code", "");
		return;
	}

	frappe.call({
		method: "hrms.organization_structure.doctype.organization_unit.organization_unit.preview_unit_code",
		args: {
			unit_type: frm.doc.unit_type,
			parent_organization_unit: frm.doc.parent_organization_unit,
			unit_name: frm.doc.unit_name,
			short_code: frm.doc.short_code,
		},
		callback(r) {
			if (!r.message) return;
			frm.set_value("unit_code", r.message.unit_code || r.message.short_code || "");
		},
	});
}

function clear_dependent_geo(frm, changed) {
	if (changed === "region" && frm.doc.zone) {
		frappe.db.get_value("Zone", frm.doc.zone, "region", (r) => {
			if (r && r.region !== frm.doc.region) {
				frm.set_value("zone", null);
				frm.set_value("city", null);
				frm.set_value("woreda", null);
			}
		});
	}
	if (changed === "zone" && frm.doc.city) {
		frappe.db.get_value("City", frm.doc.city, "zone", (r) => {
			if (r && r.zone !== frm.doc.zone) {
				frm.set_value("city", null);
				frm.set_value("woreda", null);
			}
		});
	}
}

function generate_branch_positions(frm) {
	if (!frm.doc.branch_staffing_template) {
		frappe.msgprint(__("Set a Branch Staffing Template first."));
		return;
	}

	frappe.call({
		method: "hrms.organization_structure.doctype.organization_unit.organization_unit.create_branch_positions",
		args: { organization_unit: frm.doc.name },
		freeze: true,
		freeze_message: __("Generating positions..."),
		callback(r) {
			if (!r.message) return;
			const count = r.message.count || 0;
			frappe.show_alert({
				message:
					count > 0
						? __("Created {0} vacant position(s).", [count])
						: __("All positions for this branch already exist."),
				indicator: count > 0 ? "green" : "blue",
			});
		},
	});
}

function propagate_ho_geography(frm) {
	frappe.confirm(
		__(
			"Apply this Head Office geography to all other Head Office units that inherit geography?",
		),
		() => {
			frappe.call({
				method: "hrms.organization_structure.doctype.organization_unit.organization_unit.propagate_ho_geography",
				args: { organization_unit: frm.doc.name },
				freeze: true,
				callback(r) {
					const count = r.message?.updated || 0;
					frappe.show_alert({
						message: __("Updated geography on {0} Head Office unit(s).", [count]),
						indicator: "green",
					});
				},
			});
		},
	);
}
