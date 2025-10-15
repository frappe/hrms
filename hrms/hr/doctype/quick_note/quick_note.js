// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Quick Note', {
	refresh: function(frm) {
        if (!frm.is_new()) {
            frm.add_custom_button(__('Promote to Task'), function() {
                frappe.call({
                    method: 'hrms.api.promote_note_to_task',
                    args: {
                        note_name: frm.doc.name
                    },
                    callback: function(r) {
                        if (r.message && r.message.task_name) {
                            // After successful promotion, redirect to the new task
                            frappe.set_route('Form', 'Task', r.message.task_name);
                        }
                    }
                });
            }).addClass('btn-primary');
        }
	}
});
