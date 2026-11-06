frappe.provide("hrms.appointment_letter");

hrms.appointment_letter.email = function (frm) {
	hrms.print_utils.email_with_print(frm, {
		print_format: frm.doc.appointment_letter_print_format,
		subject: __("Letter of Appointment - {0}", [frm.doc.applicant_name]),
		recipients: frm.doc.applicant_email,
		message: get_message(frm.doc),
	});
};

function get_message(doc) {
	const escape = frappe.utils.escape_html;
	const blank_line = "<p><br></p>";
	const paragraphs = [
		__("Dear {0},", [escape(doc.applicant_name)]),
		__(
			"Please find attached your letter of appointment with {0}, which sets out the terms and conditions of your employment.",
			[escape(doc.company)],
		),
		__("Please sign and return a copy of the letter as a token of your acceptance."),
	];
	return (
		paragraphs.map((line) => `<p>${line}</p>`).join(blank_line) +
		blank_line.repeat(2) +
		`<p>${__("Regards,")}</p>`
	);
}
