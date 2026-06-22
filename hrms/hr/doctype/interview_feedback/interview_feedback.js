// Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Interview Feedback", {
	onload(frm) {
		frm.ignore_doctypes_on_cancel_all = ["Interview"];

		frm.set_query("interview", () => ({
			filters: { docstatus: ["!=", 2] },
		}));
	},

	interview(frm) {
		frappe.call({
			method: "hrms.hr.doctype.interview_feedback.interview_feedback.get_applicable_interviewers",
			args: { interview: frm.doc.interview || "" },
			callback(r) {
				frm.set_query("interviewer", () => ({
					filters: { name: ["in", r.message] },
				}));
			},
		});
	},

	interviewer(frm) {
		if (!frm.doc.interview) {
			frappe.throw(__("Select Interview first"));
			frm.set_value("interviewer", "");
		}
	},

	interview_type(frm) {
		if (!frm.doc.interview_type) return;
		frappe.call({
			method: "hrms.hr.doctype.interview.interview.get_expected_skill_set",
			args: { interview_type: frm.doc.interview_type },
			callback(r) {
				frm.set_value("skill_assessment", r.message);
			},
		});
	},
});

frappe.ui.form.on("Skill Assessment", {
	rating(frm) {
		update_average_rating(frm);
	},
});

function update_average_rating(frm) {
	const rows = frm.doc.skill_assessment || [];
	const has_weightage = rows.some((row) => row.weightage);
	let total = 0;
	let divisor = 0;
	rows.forEach((row) => {
		if (!row.rating) return;
		if (has_weightage) {
			total += row.rating * (row.weightage || 0);
			divisor += row.weightage || 0;
		} else {
			total += row.rating;
			divisor += 1;
		}
	});
	frm.set_value("average_rating", divisor ? total / divisor : 0);
}
