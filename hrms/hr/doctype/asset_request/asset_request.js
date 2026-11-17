// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Asset Request", {
	refresh(frm) {
		if (frm.doc.docstatus !== 1 || frm.doc.status !== "Approved") return;

		const movement = frm.doc.__onload?.asset_movement;
		if (movement) {
			frm.add_custom_button(__("Asset Movement"), () =>
				frappe.set_route("Form", "Asset Movement", movement),
			);
			return;
		}
		frm.add_custom_button(
			__("Asset Movement"),
			() =>
				frappe.model.open_mapped_doc({
					method: "hrms.hr.doctype.asset_request.asset_request.make_asset_movement",
					frm,
				}),
			__("Create"),
		);
	},
});
