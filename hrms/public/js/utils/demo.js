frappe.provide("hrms.demo");

hrms.demo.clear_demo = function () {
	if (window.erpnext?.demo?.clear_demo) {
		return window.erpnext.demo.clear_demo();
	}

	frappe.confirm(__("Are you sure you want to clear all demo data?"), () => {
		frappe.call({
			method: "erpnext.setup.demo.clear_demo_data",
			freeze: true,
			freeze_message: __("Clearing Demo Data..."),
			callback: function () {
				frappe.ui.toolbar.clear_cache();
				frappe.show_alert({
					message: __("Demo data cleared"),
					indicator: "green",
				});
			},
		});
	});
};
