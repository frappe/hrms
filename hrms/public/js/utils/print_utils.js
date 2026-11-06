hrms.print_utils = {
	email_with_print(frm, options) {
		const composer = new frappe.views.CommunicationComposer({
			doc: frm.doc,
			frm,
			attach_document_print: true,
			...options,
		});
		composer.dialog.no_focus = true;
	},

	async render_print_preview(frm, preview_fieldname, print_format) {
		const field = frm.get_field(preview_fieldname);
		const $wrapper = field.$wrapper;
		const request = (field.preview_request = (field.preview_request || 0) + 1);
		if (!print_format) {
			$wrapper.empty();
			return;
		}

		const { message } = await frappe.call({
			method: "frappe.www.printview.get_html_and_style",
			args: {
				doc: frm.doc,
				print_format: print_format,
				letterhead: frm.doc.letter_head,
				no_letterhead: frm.doc.letter_head ? 0 : 1,
			},
		});
		if (request !== field.preview_request || !message) return;

		const $iframe = $(
			`<iframe sandbox="allow-same-origin" frameborder="0" style="width: 100%; height: 900px; border: 1px solid var(--border-color); border-radius: var(--border-radius-md);"></iframe>`,
		);
		$iframe[0].srcdoc = /^\s*<(!doctype|html)\b/i.test(message.html || "")
			? message.html
			: `<!DOCTYPE html><html><head>
				<link href="${frappe.urllib.get_base_url()}${frappe.assets.bundled_asset(
					"print.bundle.css",
				)}" rel="stylesheet">
				<style>${(message.style || "").replace(/<\//g, "<\\/")}</style>
			</head><body><div class="print-format">${message.html || ""}</div></body></html>`;

		const $head = $(`<div class="text-base-medium mb-3">${__(field.df.label)}</div>`);
		$wrapper.empty().append($head, $iframe);
	},
};
