frappe.listview_settings['Goal'] = {
	add_fields: ["due_date", "status"],
	get_indicator: function(doc) {
		const status_color = {
			'Pending': 'yellow',
			'In Progress': 'orange',
			'Completed': 'green',
			'Archived': 'gray',
		};
		return [__(doc.status), status_color[doc.status], 'status,=,'+doc.status];
	},
	formatters: {
		due_date(value, df, doc) {
			if (!value) return ''
			if (doc.status === 'Completed' || doc.status === 'Archived') return '';

			const d = moment(value);
			const now = moment();
			let color = 'green';
			if (d < now) {
				color = 'red'
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
