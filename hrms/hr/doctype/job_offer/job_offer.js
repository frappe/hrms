// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.provide("erpnext.job_offer");

frappe.ui.form.on("Job Offer", {
	onload: function (frm) {
		frm.set_query("select_terms", function() {
			return { filters: { hr: 1 } };
		});
	},

	setup: function (frm) {
		frm.email_field = "applicant_email";
	},

	select_terms: function (frm) {
		erpnext.utils.get_terms(frm.doc.select_terms, frm.doc, function (r) {
			if (!r.exc) {
				frm.set_value("terms", r.message);
			}
		});
	},
	job_offer_term_template: function (frm) {
		if (!frm.doc.job_offer_term_template) return;

		frappe.db.get_doc("Job Offer Term Template", frm.doc.job_offer_term_template).then((doc) => {
			frm.clear_table("offer_terms");
			doc.offer_terms.forEach((term) => {
				frm.add_child("offer_terms", term);
			})
			refresh_field("offer_terms");
		})

	},

	refresh: function (frm) {
		if ((!frm.doc.__islocal) && (frm.doc.status == 'Accepted')
			&& (frm.doc.docstatus === 1) && (!frm.doc.__onload || !frm.doc.__onload.employee)) {
			frm.add_custom_button(__('Create Employee'),
				function () {
					erpnext.job_offer.make_employee(frm);
				}
			);
		}

		if(frm.doc.__onload && frm.doc.__onload.employee) {
			frm.add_custom_button(__('Show Employee'),
				function () {
					frappe.set_route("Form", "Employee", frm.doc.__onload.employee);
				}
			);
		}
	}

});

erpnext.job_offer.make_employee = function (frm) {
	frappe.model.open_mapped_doc({
		method: "hrms.hr.doctype.job_offer.job_offer.make_employee",
		frm: frm
	});
};
