frappe.pages["organizational-chart"].on_page_load = function (wrapper) {
	frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Organizational Chart"),
		single_column: true,
	});

	$(wrapper).bind("show", () => {
		frappe.require("hierarchy-chart.bundle.js", () => {
			let organizational_chart;
			let method = "hrms.hr.page.organizational_chart.organizational_chart.get_children";

			if (frappe.is_mobile()) {
<<<<<<< HEAD
				organizational_chart = new erpnext.HierarchyChartMobile(
					"Employee",
					wrapper,
					method,
				);
			} else {
				organizational_chart = new erpnext.HierarchyChart("Employee", wrapper, method);
=======
				organizational_chart = new hrms.HierarchyChartMobile("Employee", wrapper, method);
			} else {
				organizational_chart = new hrms.HierarchyChart("Employee", wrapper, method);
>>>>>>> da17577dc (chore: remove unused import)
			}

			frappe.breadcrumbs.add("HR");
			organizational_chart.show();
		});
	});
};
