// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Payroll Correction and  Arrears", {
	refresh(frm) {

	},

    additional_salary_date:function(frm){
        if(frm.doc.additional_salary_date){
            console.log("additional_salary_date",frm.doc.additional_salary_date);
            console.log("today",frappe.datetime.nowdate());
            if(frm.doc.additional_salary_date < frappe.datetime.nowdate()){
                frappe.msgprint({
                    title: __("Invalid Date"),
                    message: __("You cannot select a past date for 'Additional Salary Date'."),
                    indicator: "red"
                });
                frm.set_value("additional_salary_date", undefined);
            }
        }
    },

    lwp_month_reversal_date:function(frm){
        if(lwp_month_reversal_date)
        {
            console.log(frm.doc.lwp_month_reversal_date)
        }
    },
});
