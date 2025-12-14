// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Overtime Type", {
	accrue_compensatory_off(frm) {
		if (frm.doc.accrue_compensatory_off) {
			frm.set_query("compensatory_off_component", () => {
				return {
					filters: {
						is_compensatory: true,
					},
				};
			});
		}
	},
});
