// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
let lwp_array = [];
frappe.ui.form.on("Payroll Correction", {
    additional_salary_date:function(frm){
        if(frm.doc.additional_salary_date){
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

    refresh: function (frm) {
        if (frm.doc.employee && frm.doc.payroll_period && frm.doc.company) {
            lwp_array = []; 
            frappe.call({
                method: "frappe.client.get_list",
                args: {
                    doctype: "Salary Slip",
                    filters: [
                        ["employee", "=", frm.doc.employee],
                        ["docstatus", "=", 1],
                        ["current_payroll_period", "=", frm.doc.payroll_period],
                        ["company", "=", frm.doc.company]
                    ],
                    fields: ["name", "absent_days", "leave_without_pay", "posting_date", "total_working_days"]
                },
                callback: function (res) {
                    if (res.message) {
                        let salary_slips = res.message;
                        let month_set = new Set();
    
                        salary_slips.forEach(d => {
                            if ((d.absent_days && d.absent_days > 0) || (d.leave_without_pay && d.leave_without_pay > 0)) {
                                let posting_date = new Date(d.posting_date);
                                let month_name = posting_date.toLocaleString('default', { month: 'long' });
                                month_set.add(month_name);
    
                                lwp_array.push({
                                    "salary_slip_id": d.name,
                                    "absent_days": parseInt(d.absent_days) || 0,
                                    "leave_without_pay": parseInt(d.leave_without_pay) || 0,
                                    "posting_date": d.posting_date,
                                    "month_name": month_name,
                                    "working_days": d.total_working_days,
                                });
                            }
                        });
    
                        let month_names = [""].concat(Array.from(month_set).sort());                         
                        frm.set_df_property('lwp_month_reversal', 'options', month_names.join('\n'));
                        frm.refresh_field('lwp_month_reversal');
                    } else {
                        frm.set_df_property('lwp_month_reversal', 'options', "");
                        frm.refresh_field('lwp_month_reversal');
                    }
    
                }
            });
        }

        else{
            frm.set_value("lwp_month_reversal",undefined);
            frm.set_value("salary_slip_id", undefined);
            frm.set_value("absent_days", undefined);
            frm.set_value("working_days", undefined);
            frm.set_value("lwp_days", undefined);
            
        }
    },

  
    payroll_period: function (frm) {
        if (frm.doc.employee && frm.doc.payroll_period && frm.doc.company) {
            lwp_array = []; 
            frappe.call({
                method: "frappe.client.get_list",
                args: {
                    doctype: "Salary Slip",
                    filters: [
                        ["employee", "=", frm.doc.employee],
                        ["docstatus", "=", 1],
                        ["current_payroll_period", "=", frm.doc.payroll_period],
                        ["company", "=", frm.doc.company]
                    ],
                    fields: ["name", "absent_days", "leave_without_pay", "posting_date", "total_working_days"]
                },
                callback: function (res) {
                    if (res.message) {
                        let salary_slips = res.message;
                        let month_set = new Set();
    
                        salary_slips.forEach(d => {
                            if ((d.absent_days && d.absent_days > 0) || (d.leave_without_pay && d.leave_without_pay > 0)) {
                                let posting_date = new Date(d.posting_date);
                                let month_name = posting_date.toLocaleString('default', { month: 'long' });
                                month_set.add(month_name);
    
                                lwp_array.push({
                                    "salary_slip_id": d.name,
                                    "absent_days": parseInt(d.absent_days) || 0,
                                    "leave_without_pay": parseInt(d.leave_without_pay) || 0,
                                    "posting_date": d.posting_date,
                                    "month_name": month_name,
                                    "working_days": d.total_working_days,
                                });
                            }
                        });
    
                        let month_names = [""].concat(Array.from(month_set).sort());                         
                        frm.set_df_property('lwp_month_reversal', 'options', month_names.join('\n'));
                        frm.refresh_field('lwp_month_reversal');
                    } else {
                        frm.set_df_property('lwp_month_reversal', 'options', "");
                        frm.refresh_field('lwp_month_reversal');
                    }
    
                    ["salary_slip_id", "working_days", "absent_days", "lwp_days", "total_lwp_days", "number_of_days_planning_to_reverse"]
                        .forEach(field => frm.set_value(field, undefined));
                }
            });
        }

        else{
            frm.set_value("lwp_month_reversal",undefined);
            frm.set_value("salary_slip_id", undefined);
            frm.set_value("absent_days", undefined);
            frm.set_value("working_days", undefined);
            frm.set_value("lwp_days", undefined);
            
        }
    },
    


    employee: function (frm) {
        if (frm.doc.employee && frm.doc.payroll_period && frm.doc.company) {
            lwp_array = []; 
            frappe.call({
                method: "frappe.client.get_list",
                args: {
                    doctype: "Salary Slip",
                    filters: [
                        ["employee", "=", frm.doc.employee],
                        ["docstatus", "=", 1],
                        ["current_payroll_period", "=", frm.doc.payroll_period],
                        ["company", "=", frm.doc.company]
                    ],
                    fields: ["name", "absent_days", "leave_without_pay", "posting_date", "total_working_days"]
                },
                callback: function (res) {
                    if (res.message) {
                        let salary_slips = res.message;
                        let month_set = new Set();
    
                        salary_slips.forEach(d => {
                            if ((d.absent_days && d.absent_days > 0) || (d.leave_without_pay && d.leave_without_pay > 0)) {
                                let posting_date = new Date(d.posting_date);
                                let month_name = posting_date.toLocaleString('default', { month: 'long' });
                                month_set.add(month_name);
    
                                lwp_array.push({
                                    "salary_slip_id": d.name,
                                    "absent_days": parseInt(d.absent_days) || 0,
                                    "leave_without_pay": parseInt(d.leave_without_pay) || 0,
                                    "posting_date": d.posting_date,
                                    "month_name": month_name,
                                    "working_days": d.total_working_days,
                                });
                            }
                        });
    
                        let month_names = [""].concat(Array.from(month_set).sort()); 
                        
                        frm.set_df_property('lwp_month_reversal', 'options', month_names.join('\n'));
                        frm.refresh_field('lwp_month_reversal');
                    } else {
                        frm.set_df_property('lwp_month_reversal', 'options', "");
                        frm.refresh_field('lwp_month_reversal');
                    }
    
                    ["salary_slip_id", "working_days", "absent_days", "lwp_days", "total_lwp_days", "number_of_days_planning_to_reverse"]
                        .forEach(field => frm.set_value(field, undefined));
                }
            });
        }

        else{
            frm.set_value("lwp_month_reversal",undefined);
            frm.set_value("salary_slip_id", undefined);
            frm.set_value("absent_days", undefined);
            frm.set_value("working_days", undefined);
            frm.set_value("lwp_days", undefined);
            
        }
    },
    
    lwp_month_reversal: function (frm) {
        if (frm.doc.lwp_month_reversal) {
            console.log(lwp_array, "Updated LWP Array");
            let selected_month = frm.doc.lwp_month_reversal;
            let selected_entry = lwp_array.find(entry => entry.month_name === selected_month);
            
            if (selected_entry) {
                frm.set_value("salary_slip_id", selected_entry.salary_slip_id);
                frm.set_value("absent_days", selected_entry.absent_days);
                frm.set_value("working_days", selected_entry.working_days);
                frm.set_value("lwp_days", selected_entry.leave_without_pay);
                frm.set_value("total_lwp_days", selected_entry.absent_days + selected_entry.leave_without_pay);
            }
        }
    
        if (frm.doc.lwp_month_reversal && frm.doc.docstatus === 0) {
            frm.set_value("number_of_days_planning_to_reverse", 0);
        }
    },
    number_of_days_planning_to_reverse:function(frm)
    {
        if(frm.doc.number_of_days_planning_to_reverse && frm.doc.total_lwp_days)
        {
            if(frm.doc.number_of_days_planning_to_reverse > frm.doc.total_lwp_days)
            {
                frappe.msgprint({
                    title: __("Invalid Number of Days"),
                    message: __("Number of days planning to reverse cannot be greater than total LWP days."),
                    indicator: "red"
                });
                frm.set_value("number_of_days_planning_to_reverse", undefined);
            }
        }
    },

    
});
