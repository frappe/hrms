// Copyright (c) 2023, LucrumERP and contributors
// For license information, please see license.txt

frappe.ui.form.on('Salary Revise Tool', {
	load_data: function(frm) {
			frappe.call({
				method: "hrms.hr.doctype.salary_revise_tool.salary_revise_tool.load_data",
				freeze: true,
				args: {
					"department": frm.doc.department || null,
					"branch": frm.doc.branch || null,
				},
				callback: function (r) {
					cur_frm.clear_table("employee_salary_details");
					cur_frm.refresh_fields("items");
					$.each(r.message, function (i, d) {
						var childTable = cur_frm.add_child("employee_salary_details");
						childTable.last_salary=d[0];
						childTable.from_date=d[1];
						childTable.employee=d[2];
						childTable.employee_name=d[3];
						childTable.designation=d[4];
						childTable.department=d[5];
						childTable.location=d[6];
						childTable.shift=d[7];
						childTable.last_variable = d[8];
						childTable.ref_ss_assignment = d[9];
						cur_frm.refresh_fields("employee_salary_details");
					});
				}
			});
	}
});


frappe.ui.form.on('Salary Details', {
	employee: function(frm, cdt, cdn) {
		var child = locals[cdt][cdn];
		if (child.employee) {
			frappe.call({
				method: "hrms.hr.doctype.salary_revise_tool.salary_revise_tool.fetch_employee_salary",
				args: {
					"employee": child.employee
				},
				callback: function(r) {
					let d = r.message;
					child.last_salary = d[0];
					child.from_date = d[1];
					frm.refresh_fields();
				}
			});
		}
	},
});
