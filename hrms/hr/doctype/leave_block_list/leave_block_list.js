// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Leave Block List', {
	add_day_wise_dates: function(frm) {
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
					fieldname: "days",
					fieldtype: "MultiCheck",
					select_all: true,
					columns: 3,
					reqd: 1,
					options: [
						{
							label: __("Monday"),
							value: "Monday",
							checked: 0,
						},
						{
							label: __("Tuesday"),
							value: "Tuesday",
							checked: 0,
						},
						{
							label: __("Wednesday"),
							value: "Wednesday",
							checked: 0,
						},
						{
							label: __("Thursday"),
							value: "Thursday",
							checked: 0,
						},
						{
							label: __("Friday"),
							value: "Friday",
							checked: 0,
						},
						{
							label: __("Saturday"),
							value: "Saturday",
							checked: 0,
						},
						{
							label: __("Sunday"),
							value: "Sunday",
							checked: 0,
						},
					],
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
				frm.call('set_weekly_off_dates', {
					'start_date': d.get_value('start_date'),
					'end_date': d.get_value('end_date'),
					'reason': d.get_value('reason'),
					'days': d.get_value('days')
				});
				frm.dirty();
				d.hide();
			}
		});

		d.show();
	}
});
