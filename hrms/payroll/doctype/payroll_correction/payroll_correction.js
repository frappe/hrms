// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Payroll Correction", {
	lwp_array: [],
	refresh(frm) {
		frm.trigger("load_lwp_months");
	},
	employee(frm) {
		frm.trigger("load_lwp_months");
	},
	payroll_period(frm) {
		frm.trigger("load_lwp_months");
	},

	load_lwp_months(frm) {
		if (!(frm.doc.employee && frm.doc.payroll_period && frm.doc.company)) {
			frm.set_value("month_for_lwp_reversal", undefined);
			["salary_slip_reference", "payment_days", "working_days", "lwp_days"].forEach((f) =>
				frm.set_value(f, undefined),
			);
			return;
		}

		frm.call({
			method: "fetch_salary_slip_details",
			doc: frm.doc,
			callback(res) {
				if (res.message) {
					const { months, slip_details } = res.message;
					frm.lwp_array = slip_details;
					frm.set_df_property(
						"month_for_lwp_reversal",
						"options",
						[""].concat(months).join("\n"),
					);
					frm.refresh_field("month_for_lwp_reversal");
				} else {
					frm.lwp_array = [];
					frm.set_df_property("month_for_lwp_reversal", "options", "");
					frm.refresh_field("month_for_lwp_reversal");
				}
			},
		});
	},

	month_for_lwp_reversal(frm) {
		let selected_entry = frm.lwp_array.find(
			(e) => e.month_name === frm.doc.month_for_lwp_reversal,
		);

		if (selected_entry) {
			frm.set_value("salary_slip_reference", selected_entry.salary_slip_reference);
			frm.set_value("payment_days", selected_entry.payment_days);
			frm.set_value("working_days", selected_entry.working_days);
			frm.set_value(
				"lwp_days",
				Math.max(0, selected_entry.working_days - selected_entry.payment_days),
			);
		}

		if (frm.doc.days_to_reverse && frm.doc.docstatus === 0) {
			frm.set_value("days_to_reverse", 0);
		}
	},
});
