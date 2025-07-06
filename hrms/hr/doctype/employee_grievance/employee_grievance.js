// Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Employee Grievance", {
	refresh: (frm) => {
		if (
			frm.doc.owner === frappe.session.user &&
			frm.doc.docstatus === 1 &&
			!frm.doc.against_employee_grievance
		) {
			frm.add_custom_button(__("Re-open"), () => {
				let d = new frappe.ui.Dialog({
					title: "Reason for re-open",
					fields: [
						{
							label: "Reason",
							fieldname: "reason",
							fieldtype: "Small Text",
							reqd: 1,
						},
					],
					size: "large",
					primary_action_label: "Re-open",
					primary_action(values) {
						frappe.model.with_doctype("Employee Grievance", () => {
							let employeeGrievance = frappe.model.get_new_doc("Employee Grievance");
							let fields = Object.keys(frm.doc);
							let fieldsToExclude = ["name", "docstatus"];

							fields.forEach((field) => {
								if (fieldsToExclude.includes(field)) return;
								employeeGrievance[field] = frm.doc[field];
							});
							employeeGrievance.against_employee_grievance = frm.doc.name;
							employeeGrievance.reopen_reason = values.reason;
							employeeGrievance.status = "Open";
							employeeGrievance.date = frappe.datetime.get_today();

							frappe.set_route("Form", "Employee Grievance", employeeGrievance.name);
						});
					},
				});
				d.show();
			});
		}
	},
	setup: function (frm) {
		frm.set_query("grievance_against_party", function () {
			return {
				filters: {
					name: [
						"in",
						["Company", "Department", "Employee Group", "Employee Grade", "Employee"],
					],
				},
			};
		});
		frm.set_query("associated_document_type", function () {
			let ignore_modules = [
				"Setup",
				"Core",
				"Integrations",
				"Automation",
				"Website",
				"Utilities",
				"Event Streaming",
				"Social",
				"Chat",
				"Data Migration",
				"Printing",
				"Desk",
				"Custom",
			];
			return {
				filters: {
					istable: 0,
					issingle: 0,
					module: ["Not In", ignore_modules],
				},
			};
		});
	},

	grievance_against_party: function (frm) {
		let filters = {};
		if (frm.doc.grievance_against_party == "Employee" && frm.doc.raised_by) {
			filters.name = ["!=", frm.doc.raised_by];
		}
		frm.set_query("grievance_against", function () {
			return {
				filters: filters,
			};
		});
	},
});
