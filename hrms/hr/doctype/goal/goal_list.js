frappe.listview_settings["Goal"] = {
	add_fields: ["end_date", "status"],
	get_indicator: function(doc) {
		const status_color = {
			"Pending": "yellow",
			"In Progress": "orange",
			"Completed": "green",
			"Archived": "gray",
		};
		return [__(doc.status), status_color[doc.status], "status,=," + doc.status];
	},
	formatters: {
		end_date(value, df, doc) {
			if (!value) return ""
			if (doc.status === "Completed" || doc.status === "Archived") return "";

			const d = moment(value);
			const now = moment();
			const color = d < now ? "red" : "green";

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
