// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Appraisal Template", {
	setup(frm) {
		frm.get_field("rating_criteria").grid.editable_fields = [
			{ fieldname: "criteria", columns: 6 },
			{ fieldname: "per_weightage", columns: 5 },
		];
	},
});
