frappe.listview_settings["Employee Referral"] = {
	add_fields: ["status"],
	has_indicator_for_draft: 1,
	get_indicator: function (doc) {
		// a draft isn't a problem, so it isn't red
		if (doc.docstatus === 0) {
			return [__("Draft"), "gray", "docstatus,=,0"];
		} else if (doc.status == "Pending") {
			return [__(doc.status), "grey", "status,=," + doc.status];
		} else if (doc.status == "In Process") {
			return [__(doc.status), "orange", "status,=," + doc.status];
		} else if (doc.status == "Accepted") {
			return [__(doc.status), "green", "status,=," + doc.status];
		} else if (doc.status == "Rejected") {
			return [__(doc.status), "red", "status,=," + doc.status];
		}
	},
};
