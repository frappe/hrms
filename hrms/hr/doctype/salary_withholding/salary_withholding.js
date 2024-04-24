// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Salary Withholding", {
	employee: function (frm) {
		if (frm.doc.employee) {
			frappe.db.get_doc("Employee", frm.doc.employee).then((doc) => {
				frm.doc.date_of_joining = doc.date_of_joining
				if (doc.relieving_date) {
					frm.doc.relieving_date = doc.relieving_date
				}
				else {
					const relieving_date = frappe.datetime.add_months(frappe.datetime.get_today(), months = doc.notice)
					frm.doc.relieving_date = relieving_date

				}
				refresh_field("date_of_joining")
				refresh_field("relieving_date")
			})
		}
	},
});