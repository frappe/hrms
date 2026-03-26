// Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Employee Benefit Application", {
	employee: function (frm) {
		if (frm.doc.employee) {
			frappe.run_serially([() => frm.trigger("set_earning_component")]);
		}
	},

	date: function (frm) {
		frm.trigger("set_earning_component");
	},

	set_earning_component: function (frm) {
		if (!frm.doc.date || !frm.doc.employee) {
			frm.doc.employee_benefits = [];
		} else {
			frm.call("set_benefit_components_and_currency");
		}
		frm.refresh_fields();
	},
});

frappe.ui.form.on("Employee Benefit Application Detail", {
	amount: function (frm) {
		calculate_all(frm.doc);
	},
	employee_benefits_remove: function (frm) {
		calculate_all(frm.doc);
	},
});

var calculate_all = function (doc) {
	var tbl = doc.employee_benefits || [];
	var total_amount = 0;
	if (doc.max_benefits === 0) {
		doc.employee_benefits = [];
	} else {
		for (var i = 0; i < tbl.length; i++) {
			if (cint(tbl[i].amount) > 0) {
				total_amount += flt(tbl[i].amount);
			}
		}
	}

	doc.total_amount = total_amount;
	doc.remaining_benefit = doc.max_benefits - total_amount;
	refresh_many(["total_amount", "remaining_benefit"]);
};
