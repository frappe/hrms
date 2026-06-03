// Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Job Opening", {
	onload: function (frm) {
		frm.set_query("department", function () {
			return {
				filters: {
					company: frm.doc.company,
				},
			};
		});
	},
	designation: function (frm) {
		if (frm.doc.designation) {
			frm.set_value("job_title", frm.doc.designation);
		}
		if (frm.doc.designation && frm.doc.company) {
			frappe.call({
				method: "hrms.hr.doctype.staffing_plan.staffing_plan.get_active_staffing_plan_details",
				args: {
					company: frm.doc.company,
					designation: frm.doc.designation,
					date: frappe.datetime.now_date(), // ToDo - Date in Job Opening?
				},
				callback: function (data) {
					if (data.message) {
						frm.set_value("staffing_plan", data.message[0].name);
						frm.set_value("planned_vacancies", data.message[0].vacancies);
					} else {
						frm.set_value("staffing_plan", "");
						frm.set_value("planned_vacancies", 0);
						frappe.show_alert({
							indicator: "orange",
							message: __("No Staffing Plans found for this Designation"),
						});
					}
				},
			});
		} else {
			frm.set_value("staffing_plan", "");
			frm.set_value("planned_vacancies", 0);
		}
	},
	company: function (frm) {
		frm.set_value("designation", "");
	},

	job_opening_template: function (frm) {
		if (!frm.doc.job_opening_template) return;
		frappe.db.get_doc("Job Opening Template", frm.doc.job_opening_template).then((doc) => {
			frm.set_value({
				designation: doc.designation,
				department: doc.department,
				employment_type: doc.employment_type,
				location: doc.location,
				description: doc.description,
				currency: doc.currency,
				upper_range: doc.upper_range,
				lower_range: doc.lower_range,
				salary_per: doc.salary_per,
				publish_salary_range: doc.publish_salary_range,
			});

			frm.refresh_fields();
		});
	},
	publish: function (frm) {
		if (frm.doc.publish && !frm.doc.route) {
			frm.trigger("set_route");
		}
	},
	set_route: function (frm) {
		if (frm.doc.publish && !frm.doc.route) {
			route = `jobs/${frappe.scrub(frm.doc.company)}/${frappe.scrub(frm.doc.job_title)}`;
			frm.set_value("route", route);
		}
	},
});
