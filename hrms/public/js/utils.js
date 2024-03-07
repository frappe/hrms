frappe.provide("hrms");
frappe.provide("hrms.utils");

$.extend(hrms, {
	proceed_save_with_reminders_frequency_change: () => {
		frappe.ui.hide_open_dialog();
		frappe.call({
			method:
				"hrms.hr.doctype.hr_settings.hr_settings.set_proceed_with_frequency_change",
			callback: () => {
				cur_frm.save();
			},
		});
	},

	set_payroll_frequency_to_null: (frm) => {
		if (cint(frm.doc.salary_slip_based_on_timesheet)) {
			frm.set_value("payroll_frequency", "");
		}
	},

	get_current_employee: async (frm) => {
		const employee = (
			await frappe.db.get_value(
				"Employee",
				{ user_id: frappe.session.user },
				"name"
			)
		)?.message?.name;

		return employee;
	},

	notify_bulk_action_status: (doctype, failure, success) => {
		let message = "";
		let title = __("Success");
		let indicator = "green";

		if (failure.length) {
			message += __("Failed to create/submit {0} for employees:", [doctype]);
			message += " " + frappe.utils.comma_and(failure) + "<hr>";
			message += __(
				"Check <a href='/app/List/Error Log?reference_doctype={0}'>{1}</a> for more details",
				[doctype, __("Error Log")]
			);
			title = __("Creation Failed");
			indicator = "red";

			if (success.length) {
				message += "<hr>";
				title = __("Partial Success");
				indicator = "orange";
			}
		}

		if (success.length) {
			message += __("Successfully created {0} for employees:", [doctype]);
			message += " " + frappe.utils.comma_and(success);
		}

		frappe.msgprint({
			message,
			title,
			indicator,
			is_minimizable: true,
		});
	},
});
