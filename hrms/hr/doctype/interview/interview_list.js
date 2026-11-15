frappe.listview_settings["Interview"] = {
	has_indicator_for_draft: 1,
	// an interview is known by its applicant and round
	hide_name_column: true,
	get_indicator: function (doc) {
		let status_color = {
			Pending: "orange",
			"Under Review": "blue",
			Cleared: "green",
			Rejected: "red",
			Cancelled: "red",
		};
		return [__(doc.status), status_color[doc.status], "status,=," + doc.status];
	},
};
