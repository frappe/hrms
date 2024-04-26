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
	from_date: function (frm) {
		if (frm.doc.number_of_withholding_cycles) {
			from_date = frm.doc.from_date
			frappe.db.get_list("Salary Structure Assignment", {
				filters: {
					employee: frm.doc.employee
				},
				fields: ["salary_structure"],
				order_by: "from_date desc"
			}).then((data) => {
				frappe.db.get_value("Salary Structure", data[0].salary_structure, "payroll_frequency").then((r) => {
					switch (r.message.payroll_frequency) {
						case "Monthly":
							console.log("monthly")
							frm.doc.to_date = frappe.datetime.add_months(from_date, months = frm.doc.number_of_withholding_cycles)
							break
						case "Bimonthly":
							console.log("bimonthly")
							frm.doc.to_date = frappe.datetime.add_months(from_date, months = frm.doc.number_of_withholding_cycles * 2)
							break
						case "Weekly":
							console.log("weekly")
							frm.doc.to_date = frappe.datetime.add_days(from_date, days = frm.doc.number_of_withholding_cycles * 7)
							break
						case "Fortnightly":
							console.log("fortnightly")
							frm.doc.to_date = frappe.datetime.add_days(from_date, days = frm.doc.number_of_withholding_cycles * 14)
							break
						case "Daily":
							console.log("daily")
							frm.doc.to_date = frappe.datetime.add_days(from_date, days = frm.doc.number_of_withholding_cycles)
					}
					refresh_field("to_date")
				})
			})
		}
	}
});