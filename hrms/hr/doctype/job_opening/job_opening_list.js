frappe.listview_settings["Job Opening"] = {
	// an opening is known by its role, department and location
	hide_name_column: true,
	get_indicator: function (doc) {
		return [
			__(doc.status),
			doc.status === "Open" ? "green" : "gray",
			`status,=,${doc.status}`,
		];
	},
};
