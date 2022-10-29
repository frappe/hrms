// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Leave Block List', {
	refresh: function(frm) {
		frm.add_custom_button(__("Bulk Add Dates"), function () {
			let d = new frappe.ui.Dialog({
				title: 'Add Leave Block Dates',
				fields: [
					{
						label: 'Start Date',
						fieldname: 'start_date',
						fieldtype: 'Date',
						reqd: 1
					},
					{
						fieldname: 'col_break_0',
						fieldtype: 'Column Break'
					},
					{
						label: 'End Date',
						fieldname: 'end_date',
						fieldtype: 'Date',
						reqd: 1
					},
					{
						fieldname: 'sec_break_0',
						fieldtype: 'Section Break'
					},
					{
						label: 'Monday',
						fieldname: 'monday',
						fieldtype: 'Check'
					},
					{
						label: 'Thursday',
						fieldname: 'thursday',
						fieldtype: 'Check'
					},
					{
						label: 'Sunday',
						fieldname: 'sunday',
						fieldtype: 'Check'
					},
					{
						fieldname: 'col_break_0',
						fieldtype: 'Column Break'
					},
					{
						label: 'Tuesday',
						fieldname: 'tuesday',
						fieldtype: 'Check'
					},
					{
						label: 'Friday',
						fieldname: 'friday',
						fieldtype: 'Check'
					},
					{
						fieldname: 'col_break_0',
						fieldtype: 'Column Break'
					},
					{
						label: 'Wednesday',
						fieldname: 'wednesday',
						fieldtype: 'Check'
					},
					{
						label: 'Saturday',
						fieldname: 'saturday',
						fieldtype: 'Check'
					},
					{
						fieldname: 'sec_break_0',
						fieldtype: 'Section Break'
					},
					{
						label: 'Reason',
						fieldname: 'reason',
						fieldtype: 'Small Text',
						reqd: 1
					},
				],
				primary_action_label: 'Add',
				primary_action(values) {
					let days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
					frm.call('get_weekly_off_dates', {
						'start_date': d.get_value('start_date'),
						'end_date': d.get_value('end_date'),
						'reason': d.get_value('reason'),
						'days': days.map(function(item) {
							if (d.get_value(frappe.scrub(item))) return item
						})
					});
					frm.dirty();
					d.hide();
				}
			});

			d.show();
		});
	}
});
