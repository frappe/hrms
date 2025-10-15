// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Task', {
	refresh: function(frm) {
        if (!frm.is_new()) {
            frm.add_custom_button(__('Log Time'), function() {
                frappe.prompt([
                    {
                        fieldname: 'hours',
                        label: 'Hours',
                        fieldtype: 'Float',
                        reqd: 1
                    },
                    {
                        fieldname: 'description',
                        label: 'Description',
                        fieldtype: 'Text'
                    }
                ], function(values){
                    // Add a new row to the 'time_logs' child table
                    let row = frm.add_child('time_logs', {
                        'hours': values.hours,
                        'description': values.description
                    });
                    frm.refresh_field('time_logs');

                    // Save the form to trigger the backend calculation
                    frm.save();
                }, 'Log Time on Task');
            }).addClass('btn-primary');
        }
	}
});
