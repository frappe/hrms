// Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Appraisal Cycle", {
	refresh(frm) {
		frm.set_query("department", () => {
			return {
				filters: {
					company: frm.doc.company
				}
			}
		});

		frm.trigger("show_custom_buttons");
	},

	show_custom_buttons(frm) {
		if (frm.doc.__islocal) return;

		frm.add_custom_button(__("View Goals"), () => {
			frappe.route_options = {
				company: frm.doc.company,
				appraisal_cycle: frm.doc.name,
			};
			frappe.set_route("Tree", "Goal");
		});

		let className = "";

		if (frm.doc.status !== "Completed") {
			className = (frm.doc.__onload?.appraisals_created) ? "btn-default": "btn-primary";

			frm.add_custom_button(__("Create Appraisals"), () => {
				frm.trigger("create_appraisals");
			}).addClass(className);
		}

		if (frm.doc.status === "Not Started") {
			className = (frm.doc.__onload?.appraisals_created) ? "btn-primary": "btn-default";

			frm.add_custom_button(__("Start"), () => {
				frm.set_value("status", "In Progress");
				frm.save();
			}).addClass(className);
		} else if (frm.doc.status === "In Progress") {
			frm.add_custom_button(__("Mark as Completed"), () => {
				frm.trigger("complete_cycle");
			}).addClass("btn-primary");
		} else if (frm.doc.status === "Completed") {
			frm.add_custom_button(__("Mark as In Progress"), () => {
				frm.set_value("status", "In Progress");
				frm.save();
			});
		}
	},

	get_employees(frm) {
		frappe.call({
			method: "set_employees",
			doc: frm.doc,
			freeze: true,
			freeze_message: __("Fetching Employees"),
			callback: function() {
				refresh_field("appraisees");
				frm.dirty();
			}
		});
	},

	create_appraisals(frm) {
		frm.call({
			method: "create_appraisals",
			doc: frm.doc,
			freeze: true,
		}).then((r) => {
			if (!r.exc) {
				frm.reload_doc();
			}
		});
	},

	complete_cycle(frm) {
		let msg = __("This action will prevent making changes to the linked appraisal feedback/goals.");
		msg += "<br>";
		msg += __("Are you sure you want to proceed?");

		frappe.confirm(
			msg,
			() => {
				frm.call({
					method: "complete_cycle",
					doc: frm.doc,
					freeze: true,
				}).then((r) => {
					if (!r.exc) {
						frm.reload_doc();
					}
				});
			}
		);
	},
});
