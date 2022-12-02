// Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Auto Leave Allocation', {
	setup: function(frm) {
		frappe.model.with_doctype("Employee");
	},
	refresh: function(frm) {
		frm.trigger("render_filters_table");
		if (frm.doc.docstatus === 1) {
			frm.add_custom_button(__("Allocate"), function () {
				frm.call('run_allocation')
			});
		}
	},
	render_filters_table: function (frm) {
		let wrapper = $(frm.get_field("filters_json").wrapper).empty();
		let table = $(`<table class="table table-bordered" style="cursor:pointer; margin:0px;">
			<thead>
				<tr>
					<th>${__("Filter")}</th>
					<th>${__("Condition")}</th>
					<th>${__("Value")}</th>
				</tr>
			</thead>
			<tbody></tbody>
		</table>`).appendTo(wrapper);
		$(`<p class="text-muted small">${__("Click table to edit")}</p>`).appendTo(wrapper);

		let filters = JSON.parse(frm.doc.filters_json || "[]");
		var filters_set = false;

		let fields = [
			{
				fieldtype: "HTML",
				fieldname: "filter_area",
			},
		];

		if (filters.length > 0) {
			filters.forEach((filter) => {
				const filter_row = $(`<tr>
						<td>${filter[1]}</td>
						<td>${filter[2] || ""}</td>
						<td>${filter[3]}</td>
					</tr>`);

				table.find("tbody").append(filter_row);
				filters_set = true;
			});
		}


		if (!filters_set) {
			const filter_row = $(`<tr><td colspan="3" class="text-muted text-center">
				${__("Click to Set Filters")}</td></tr>`);
			table.find("tbody").append(filter_row);
		}

		table.on("click", () => {
			frm.doc.docstatus === 1 && frappe.throw(__("Cannot edit filters for submitted document."));

			let dialog = new frappe.ui.Dialog({
				title: __("Set Filters"),
				fields: fields,
				primary_action: function () {
					let values = this.get_values();
					if (values) {
						this.hide();
						let filters = frm.filter_group.get_filters();
						frm.set_value("filters_json", JSON.stringify(filters));
						frm.trigger("render_filters_table");
					}
				},
				primary_action_label: "Set",
			});
			frappe.dashboards.filters_dialog = dialog;

			frm.filter_group = new frappe.ui.FilterGroup({
				parent: dialog.get_field("filter_area").$wrapper,
				doctype: "Employee",
				on_change: () => { },
			});

			frm.filter_group.add_filters_to_filter_group(filters);
			dialog.show();
			dialog.set_values(filters);
		});
	},
});
