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

	render_print_preview(frm, preview_fieldname, print_format) {
		const field = frm.get_field(preview_fieldname);
		return this.render_print_html(field.$wrapper, frm.doc, print_format, field.df.label);
	},

	async render_print_html($wrapper, doc, print_format, label) {
		const request = ($wrapper.data("preview_request") || 0) + 1;
		$wrapper.data("preview_request", request);
		if (!print_format) {
			$wrapper.empty();
			return;
		}

		const { message } = await frappe.call({
			method: "frappe.www.printview.get_html_and_style",
			args: {
				doc: doc,
				print_format: print_format,
				letterhead: doc.letter_head,
				no_letterhead: doc.letter_head ? 0 : 1,
			},
		});
		if (request !== $wrapper.data("preview_request") || !message) return;

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

		$wrapper.empty();
		if (label) $wrapper.append($('<div class="text-base-medium mb-3">').text(__(label)));
		$wrapper.append($iframe);
	},
};
