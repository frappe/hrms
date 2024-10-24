// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

// For license information, please see license.txt

// for communication
cur_frm.email_field = "email_id";

frappe.ui.form.on("Job Applicant", {
	refresh: function (frm) {
		frm.set_query("job_title", function () {
			return {
				filters: {
					status: "Open",
				},
			};
		});
		frm.events.create_custom_buttons(frm);
		frm.events.make_dashboard(frm);
	},

	create_custom_buttons: function (frm) {
		if (!frm.doc.__islocal && frm.doc.status !== "Rejected" && frm.doc.status !== "Accepted") {
			frm.add_custom_button(
				__("Interview"),
				function () {
					frm.events.create_dialog(frm);
				},
				__("Create"),
			);
		}

		if (!frm.doc.__islocal && frm.doc.status == "Accepted") {
			if (frm.doc.__onload && frm.doc.__onload.job_offer) {
				$('[data-doctype="Employee Onboarding"]').find("button").show();
				$('[data-doctype="Job Offer"]').find("button").hide();
				frm.add_custom_button(
					__("Job Offer"),
					function () {
						frappe.set_route("Form", "Job Offer", frm.doc.__onload.job_offer);
					},
					__("View"),
				);
			} else {
				$('[data-doctype="Employee Onboarding"]').find("button").hide();
				$('[data-doctype="Job Offer"]').find("button").show();
				frm.add_custom_button(
					__("Job Offer"),
					function () {
						frappe.route_options = {
							job_applicant: frm.doc.name,
							applicant_name: frm.doc.applicant_name,
							designation: frm.doc.job_opening || frm.doc.designation,
						};
						frappe.new_doc("Job Offer");
					},
					__("Create"),
				);
			}
		}
	},

	make_dashboard: function (frm) {
		frappe.call({
			method: "hrms.hr.doctype.job_applicant.job_applicant.get_interview_details",
			args: {
				job_applicant: frm.doc.name,
			},
			callback: function (r) {
				if (r.message) {
					$("div").remove(".form-dashboard-section.custom");
					frm.dashboard.add_section(
						frappe.render_template("job_applicant_dashboard", {
							data: r.message.interviews,
							number_of_stars: r.message.stars,
						}),
						__("Interview Summary"),
					);
				}
			},
		});
	},

	create_dialog: function (frm) {
        let d = new frappe.ui.Dialog({
            title: "Enter Interview Round",
            fields: [
                {
                    label: "Interview Round",
                    fieldname: "interview_round",
                    fieldtype: "Link",
                    options: "Interview Round",
                    reqd: 1,
                    in_list_view: 1,
                    in_standard_filter: 1
                },
                {
                    label: "Scheduled On",
                    fieldname: "scheduled_on",
                    fieldtype: "Date",
                    reqd: 1,
                    in_list_view: 1,
                    in_standard_filter: 1,
                },
                {
                    label: "Interview Start Time",
                    fieldname: "from_time",
                    fieldtype: "Time",
                    reqd: 1
                },
                {
                    label: "Interview End Time",
                    fieldname: "to_time",
                    fieldtype: "Time",
                    reqd: 1
                },
                {
                    label: "Interviewer",
                    fieldname: "interviewer",
                    fieldtype: "Link",
                    options: "User",
                    reqd: 0
                },
            ],
            primary_action_label: __("Create Interview"),
            primary_action(values) {
                // console.log("Dialog Values:", values); // Debugging line to check values
                frm.events.create_interview(frm, values);
                d.hide();
            },
        });
        d.show();
    },
    create_interview: function (frm, values) {
        console.log("Create Interview Values:", values);
        if (!values.scheduled_on || !values.from_time || !values.to_time) {
            frappe.show_alert({message: __('Scheduled date or interview time is required'), indicator: 'red'});
            return;
        }
        let scheduledDate = new Date(values.scheduled_on);
        frappe.call({
            method: "hrms.hr.doctype.job_applicant.job_applicant.create_interview",
            type: "POST",
            args: {
                doc: frm.doc,
                interview_round: values.interview_round,
                scheduled_on: scheduledDate.toISOString().split('T')[0],
                from_time: values.from_time,
                to_time: values.to_time,
                interviewer: values.interviewer  // Add this line to include the interviewer
            },
            callback: function (r) {
                if (r.message) {
                    var doclist = frappe.model.sync(r.message);
                    var doc = doclist[0];
                    // Update the document with the values from the dialog
                    frappe.model.set_value(doc.doctype, doc.name, 'scheduled_on', values.scheduled_on);
                    frappe.model.set_value(doc.doctype, doc.name, 'from_time', values.from_time);
                    frappe.model.set_value(doc.doctype, doc.name, 'to_time', values.to_time);
                    let child = frappe.model.add_child(doc, 'interview_details', 'interview_details');
                    frappe.model.set_value(child.doctype, child.name, 'interviewer', values.interviewer);
                    // Save the document
                    frappe.call({
                        method: 'frappe.desk.form.save.savedocs',
                        args: {
                            doc: doc,
                            action: 'Save'
                        },
                        callback: function(r) {
                            if (r.exc) {
                                frappe.msgprint(__("There were errors while saving. Please try again."));
                            } else {
                                frappe.show_alert({message: __('Interview created and saved successfully'), indicator: 'green'});
                                frm.refresh();
                            }
                        }
                    });
                } else {
                    console.error("Failed to create interview:", r);
                    frappe.show_alert({message: __('Failed to create interview'), indicator: 'red'});
                }
            },
        });
    }
});
