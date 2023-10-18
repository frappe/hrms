frappe.listview_settings["Goal"] = {
	add_fields: ["end_date", "status"],

	get_indicator: function (doc) {
		const status_color = {
			Pending: "yellow",
			"In Progress": "orange",
			Completed: "green",
			Archived: "gray",
			Closed: "red",
		};
		return [__(doc.status), status_color[doc.status], "status,=," + doc.status];
	},

	formatters: {
		end_date(value, df, doc) {
			if (!value) return "";
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
		},
	},

	onload: function (listview) {
		const status_menu = listview.page.add_custom_button_group(
			__("Update Status")
		);

		listview.page.add_custom_menu_item(status_menu, __("Complete"), () =>
			this.trigger_update_status_dialog("Completed", listview)
		);

		listview.page.add_custom_menu_item(status_menu, __("Archive"), () =>
			this.trigger_update_status_dialog("Archived", listview)
		);

		listview.page.add_custom_menu_item(status_menu, __("Close"), () =>
			this.trigger_update_status_dialog("Closed", listview)
		);
	},

	trigger_update_status_dialog: function (status, listview) {
		const checked_items = listview.get_checked_items();
		if (!checked_items.length) {
			frappe.throw(__("No items selected"));
			return;
		}

		if (checked_items.some((item) => item.is_group))
			frappe.msgprint({
				message: __("Cannot update status of Group Goals"),
				indicator: "orange",
			});

		if (checked_items.some((item) => item.status === "Completed"))
			frappe.msgprint({
				message: __("Cannot update status of Completed Goals"),
				indicator: "orange",
			});

		const items_to_be_completed = checked_items
			.filter(
				(item) =>
					item.status != "Completed" && item.status != status && !item.is_group
			)
			.map((item) => item.name);

		if (items_to_be_completed.length)
			frappe.confirm(
				__(
					`Mark ${items_to_be_completed.length.toString()} ${
						items_to_be_completed.length === 1 ? "item" : "items"
					} as ${status}?`
				),
				() => {
					this.update_status(status, items_to_be_completed, listview);
				}
			);
	},

	update_status: function (status, goals, listview) {
		frappe
			.call({
				method: "hrms.hr.doctype.goal.goal.update_status",
				args: {
					status: status,
					goals: goals,
				},
			})
			.then((r) => {
				if (!r.exc && r.message) {
					frappe.show_alert({
						message: __("Goals updated successfully"),
						indicator: "green",
					});
				} else {
					frappe.msgprint(__("Could not update goals"));
				}
				listview.clear_checked_items();
				listview.refresh();
			});
	},
};
