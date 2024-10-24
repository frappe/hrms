// Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
frappe.views.calendar["Attendance"] = {
	field_map: {
		start: "attendance_date",
		end: "attendance_date",
		id: "name",
		title: "title",
		allDay: "allDay",
		color: "color",
	},
	get_css_class: function (data) {
		if (data.doctype === "Holiday") return "default";
		else if (data.doctype === "Attendance") {
			if (data.status === "Absent" || data.status === "On Leave") {
				return "danger";
			}
			if (data.status === "Half Day") return "warning";
			return "success";
		}
	},
	options: {
		header: {
			left: "prev,next today",
			center: "title",
			right: "month",
		},
	},
	get_events_method: "hrms.hr.doctype.attendance.attendance.get_events",
};
