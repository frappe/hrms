frappe.listview_settings["Hiring Request"] = {
	get_indicator: function(doc) {
		const status_color = {
			"Draft": "yellow",
			"Open & Approved": "blue",
			"Rejected": "red",
			"Filled": "green",
			"Cancelled": "gray",
			"On Hold": "gray"
		};
		return [__(doc.status), status_color[doc.status], "status,=,"+doc.status];
	},
	formatters: {
		expected_by(value, df, doc) {
			if (!value) return ""
			if (["Filled", "Cancelled", "On Hold"].includes(doc.status)) return "";

			const d = moment(value);
			const now = moment();
			let color = "green";
			if (d < now) {
				color = "red"
			}

			return `
				<div
					class="pill"
					style="background-color: var(--bg-${color}); color: var(--text-on-${color}); font-weight:500">
					${d.fromNow()}
				</div>
			`;
		}
	}
}
