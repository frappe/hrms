// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Leave Adjustment", {
	refresh(frm) {
		hrms.leave_utils.add_view_ledger_button(frm);

		frm.set_query("leave_type", () => {
			return {
				query: "hrms.hr.doctype.leave_adjustment.leave_adjustment.get_allocated_leave_types",
				filters: {
					employee: frm.doc.employee,
				},
			};
		});
	},
	employee(frm) {
		if (frm.doc.employee) {
			frm.trigger("set_leave_allocation");
		}
	},
	leave_type(frm) {
		if (frm.doc.leave_type) {
			frm.trigger("set_leave_allocation");
		}
	},

	posting_date(frm) {
		if (frm.doc.posting_date) frm.trigger("set_leave_allocation");
	},

	set_leave_allocation: function (frm) {
		if (frm.doc.posting_date && frm.doc.employee && frm.doc.leave_type) {
			frappe.call({
				method: "hrms.hr.doctype.leave_adjustment.leave_adjustment.get_leave_allocation_for_posting_date",
				args: {
					posting_date: frm.doc.posting_date,
					employee: frm.doc.employee,
					leave_type: frm.doc.leave_type,
				},
				callback: function (r) {
					if (r.message?.length) {
						frm.set_value("leave_allocation", r.message[0].name);
					} else {
						frappe.msgprint(
							__("No leave allocation found for {0} for {1} on given date.", [
								frm.doc.employee_name,
								frm.doc.leave_type,
							]),
						);
						frm.set_value("leave_allocation", null);
					}
				},
			});
		}
	},
});
