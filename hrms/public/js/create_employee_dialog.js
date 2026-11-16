import {
	RecordTabsDialog,
	insert_quietly,
	is_editable,
	make_panel_body,
} from "./record_tabs_dialog.js";

const JOB_FIELDS = [
	"company",
	"date_of_joining",
	"designation",
	"department",
	"employment_type",
	"grade",
	"branch",
	"reports_to",
];
const PHOTO_FIELD = "image";
const NAME_FIELDS = ["first_name", "middle_name", "last_name"];
const EMAIL_FIELDS = ["personal_email", "company_email"];
const WHOLE_TABS = ["salary_information"];

export class CreateEmployeeDialog extends RecordTabsDialog {
	constructor({ employee, on_created }) {
		super("Employee", employee);
		if (!this.doc.salary_mode && this.doc.bank_ac_no) this.doc.salary_mode = "Bank";
		this.details = employee.__onload?.employee_details || { fields: [], documents: [] };
		this.on_created = on_created;
	}

	make_tabs() {
		const shown = new Set([...JOB_FIELDS, ...this.details.fields].filter(is_reviewable));
		return [
			...this.make_field_tabs(
				(df, tab) =>
					shown.has(df.fieldname) || (WHOLE_TABS.includes(tab) && is_editable(df)),
			),
			{
				label: __("Documents"),
				content: make_panel_body().append(this.make_documents()),
			},
		];
	}

	setup_group(group) {
		const render = () => this.render_profile();
		this.watch_fields(
			group,
			Object.fromEntries([...NAME_FIELDS, ...EMAIL_FIELDS].map((field) => [field, render])),
		);
	}

	get_actions() {
		return [{ label: __("Create Employee"), variant: "solid", onclick: () => this.create() }];
	}

	get_profile() {
		return {
			name: NAME_FIELDS.map((fieldname) => this.get_value(fieldname))
				.filter(Boolean)
				.join(" "),
			email: EMAIL_FIELDS.map((fieldname) => this.get_value(fieldname)).find(Boolean),
			image: this.doc.image,
		};
	}

	make_avatar() {
		return $(
			'<div class="profile-avatar-upload relative flex shrink-0 rounded-full overflow-hidden cursor-pointer">',
		)
			.attr("title", __("Upload Photo"))
			.on("click", () => this.upload_photo());
	}

	render_profile() {
		super.render_profile();
		this.$avatar.append(
			$(
				'<div class="profile-avatar-overlay absolute inset-0 flex items-center justify-center">',
			).append(frappe.utils.icon("camera", "md")),
		);
	}

	upload_photo() {
		new frappe.ui.FileUploader({
			allow_multiple: false,
			restrictions: { allowed_file_types: ["image/*"] },
			on_success: (file) => {
				this.doc.image = file.file_url;
				this.render_profile();
			},
		});
	}

	make_documents() {
		if (!this.details.name) {
			return frappe.ui.empty_state({
				icon: "file",
				title: __("No documents yet"),
				description: __("Documents are collected after Create User Login."),
			});
		}
		if (!this.details.documents.length) {
			return frappe.ui.empty_state({
				icon: "file",
				title: __("No documents requested"),
				description: __("The onboarding template asks for no documents."),
			});
		}
		return $("<div>").append(
			this.details.documents.map((document) => this.make_document(document)),
		)[0];
	}

	make_document(document) {
		const $row = $('<div class="epc-document">').append(
			frappe.utils.icon("file", "sm"),
			$('<span class="epc-document-name">').text(document.label),
		);
		const $status = $('<span class="epc-document-status">').appendTo($row);
		if (document.url) {
			$status.append(
				$('<a target="_blank" rel="noopener">')
					.attr("href", document.url)
					.text(__("View")),
			);
		} else {
			$status.append(
				$('<span class="indicator-pill">')
					.addClass(document.required ? "red" : "gray")
					.text(document.required ? __("Required") : __("Not uploaded")),
			);
		}
		return $row.append(
			$('<button class="btn btn-default btn-xs epc-document-action">')
				.text(document.url ? __("Replace") : __("Upload"))
				.on("click", () => this.upload_document(document, $row)),
		);
	}

	upload_document(document, $row) {
		new frappe.ui.FileUploader({
			doctype: "Employee Request",
			docname: this.details.name,
			fieldname: "attachment",
			allow_multiple: false,
			on_success: async (file) => {
				await frappe.xcall("frappe.client.set_value", {
					doctype: "Employee Boarding Document",
					name: document.row,
					fieldname: "attachment",
					value: file.file_url,
				});
				document.url = file.file_url;
				$row.replaceWith(this.make_document(document));
			},
		});
	}

	async create() {
		const values = this.get_doc();
		if (!values) return;
		const doc = await insert_quietly(values);
		if (!doc) return;
		this.dialog.hide();
		this.on_created(doc);
	}
}

function is_reviewable(fieldname) {
	return fieldname !== PHOTO_FIELD && frappe.meta.has_field("Employee", fieldname);
}
