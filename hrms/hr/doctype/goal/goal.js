// Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Goal", {
	refresh(frm) {
		frm.trigger("set_filters");
		frm.trigger("add_custom_buttons");

		if (frm.doc.is_group) {
			frm.set_df_property(
				"progress",
				"description",
				__("Group goal's progress is auto-calculated based on the child goals.")
			);
		}
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
					employee: frm.doc.employee,
					appraisal_cycle: frm.doc.appraisal_cycle,
				}
			};
		});

		frm.set_query("appraisal_cycle", () => {
			return {
				filters: {
					status: ["!=", "Completed"],
					company: frm.doc.company,
				}
			};
		});
	},

	add_custom_buttons(frm) {
		if (frm.doc.__islocal || frm.doc.status === "Completed") return;
		const doc_status = frm.doc.status;

		if (doc_status === "Archived") {
			frm.add_custom_button(__("Unarchive"), () => {
				frm.set_value("status", "");
				frm.save();
			}, __("Status"));
		}

		if (doc_status === "Closed") {
			frm.add_custom_button(__("Reopen"), () => {
				frm.set_value("status", "");
				frm.save();
			}, __("Status"));
		}

		if (doc_status !== "Archived") {
			frm.add_custom_button(__("Archive"), () => {
				frm.set_value("status", "Archived");
				frm.save();
			}, __("Status"));
		}

		if (doc_status !== "Closed") {
			frm.add_custom_button(__("Close"), () => {
				frm.set_value("status", "Closed");
				frm.save();
			}, __("Status"));
		}
	},

	kra(frm) {
		if (!frm.doc.appraisal_cycle) {
			frm.set_value("kra", "");

			frappe.msgprint({
				message: __("Please select the Appraisal Cycle first."),
				title: __("Mandatory")
			});

			return;
		}

		if (frm.doc.__islocal || !frm.doc.is_group) return;

		let msg = __("Changing KRA in this parent goal will align all the child goals to the same KRA, if any.");
		msg += "<br>";
		msg += __("Do you still want to proceed?");

		frappe.confirm(
			msg,
			() => {},
			() => {
				frappe.db.get_value("Goal", frm.doc.name, "kra", (r) => frm.set_value("kra", r.kra));
			}
		);
	},

	is_group(frm) {
		if (frm.doc.__islocal && frm.doc.is_group) {
			frm.set_value("progress", 0);
		}
	}
});
