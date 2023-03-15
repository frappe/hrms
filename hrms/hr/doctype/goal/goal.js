// Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Goal", {
	refresh(frm) {
		frm.trigger("set_filters");
		frm.trigger("add_custom_buttons");
	},

	set_filters(frm) {
		frm.set_query("parent_goal", () => {
			return {
				filters: {
					is_group: 1,
					name: ["!=", frm.doc.name],
					employee: frm.doc.employee,
				}
			}
		});

		frm.set_query("kra", () => {
			return {
				query: "hrms.hr.doctype.appraisal.appraisal.get_kras_for_employee",
				filters: {
					"employee": frm.doc.employee,
					"appraisal_cycle": frm.doc.appraisal_cycle,
				}
			};
		})
	},

	add_custom_buttons(frm) {
		if (!frm.doc.__islocal) {
			if (frm.doc.status !== "Archived") {
				frm.add_custom_button(__("Archive"), () => {
					frm.set_value("status", "Archived");
					frm.save();
				});
			} else {
				frm.add_custom_button(__("Unarchive"), () => {
					frm.set_value("status", "");
					frm.save();
				});
			}
		}
	},
});
