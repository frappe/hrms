// Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

frappe.listview_settings["Job Offer"] = {
	add_fields: ["company", "designation", "job_applicant", "status"],
	// an offer is known by its applicant and role
	hide_name_column: true,
	has_indicator_for_draft: 1,
	get_indicator: function (doc) {
		if (doc.status == "Draft") {
			return [__(doc.status), "gray", "status,=," + doc.status];
		} else if (doc.status == "Ready to Send") {
			return [__(doc.status), "blue", "status,=," + doc.status];
		} else if (doc.status == "Accepted") {
			return [__(doc.status), "green", "status,=," + doc.status];
		} else if (doc.status == "Awaiting Response") {
			return [__(doc.status), "orange", "status,=," + doc.status];
		} else if (["Rejected", "Cancelled"].includes(doc.status)) {
			return [__(doc.status), "red", "status,=," + doc.status];
		}
	},
};
