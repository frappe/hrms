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

		listview.page.add_custom_menu_item(status_menu, __("Unarchive"), () =>
			this.trigger_update_status_dialog("Unarchived", listview)
		);

		listview.page.add_custom_menu_item(status_menu, __("Reopen"), () =>
			this.trigger_update_status_dialog("Reopened", listview)
		);
	},

	trigger_update_status_dialog: function (status, listview) {
		const checked_items = listview.get_checked_items();
		const items_to_be_updated = checked_items
			.filter(
				(item) =>
					!item.is_group &&
					applicable_current_statuses(status).includes(item.status)
			)
			.map((item) => item.name);

		if (items_to_be_updated.length) {
			if (status === "Unarchived" || status === "Reopened") {
				const simple_present_tense = {
					Unarchived: "Unarchive",
					Reopened: "Reopen",
				};
				frappe.confirm(
					__(
						`${
							simple_present_tense[status]
						} ${items_to_be_updated.length.toString()} ${
							items_to_be_updated.length === 1 ? "item" : "items"
						}?`
					),
					() => {
						this.update_status("", items_to_be_updated, listview);
						this.trigger_error_dialogs(checked_items, status);
					}
				);
			} else
				frappe.confirm(
					__(
						`Mark ${items_to_be_updated.length.toString()} ${
							items_to_be_updated.length === 1 ? "item" : "items"
						} as ${status}?`
					),
					() => {
						this.update_status(status, items_to_be_updated, listview);
						this.trigger_error_dialogs(checked_items, status);
					}
				);
		} else this.trigger_error_dialogs(checked_items, status);
	},

	trigger_error_dialogs: function (checked_items, status) {
		if (!checked_items.length) {
			frappe.throw(__("No items selected"));
			return;
		}

		if (checked_items.some((item) => item.is_group))
			frappe.msgprint({
				message: __("Cannot update status of Goal groups"),
				indicator: "yellow",
			});

		const applicable_statuses = applicable_current_statuses(status);
		if (
			checked_items.some((item) => !applicable_statuses.includes(item.status))
		)
			frappe.msgprint({
				message: __(
					`Only ${frappe.utils.comma_and(
						applicable_statuses
					)} Goals can be ${status}`
				),
				indicator: "yellow",
			});
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

// Returns all possible current statuses that can be changed to the new one
const applicable_current_statuses = (new_status) => {
	switch (new_status) {
		case "Completed":
			return ["Pending", "In Progress"];
		case "Archived":
			return ["Pending", "In Progress", "Closed"];
		case "Closed":
			return ["Pending", "In Progress", "Archived"];
		case "Unarchived":
			return ["Archived"];
		case "Reopened":
			return ["Closed"];
	}
};
