hrms.organizational_chart = hrms.organizational_chart || {};

Object.assign(hrms.organizational_chart, {
	get_employee_count(company) {
		const args = {
			doctype: "Employee",
		};

		if (company) {
			args.filters = { company };
		}

		return frappe
			.call({
				method: "frappe.client.get_count",
				args,
			})
			.then((r) => Number(r.message) || 0);
	},

	clear_empty_state(page) {
		page.body.find("#hierarchy-empty-root").remove();
	},

	render_empty_state({ page, doctype, company, device_type }) {
		this.clear_empty_state(page);

		const empty = frappe.render_template("hierarchy_empty_state", {
			doctype,
			company: company || __("the selected company"),
			can_create: frappe.model.can_create(doctype),
			device_type,
		});

		page.main.append(empty);

		page.body
			.find("#add-doc-btn")
			.off("click")
			.on("click", () => {
				frappe.route_options = { company };
				frappe.new_doc(doctype);
			});
	},

	set_main_state(page, state) {
		const state_classes =
			"hierarchy-main-chart hierarchy-main-empty hierarchy-main-export hierarchy-main-mobile-chart hierarchy-main-mobile-empty";
		page.main.removeClass(state_classes);

		if (state) {
			page.main.addClass(state);
		}
	},

	get_state_config(device_type) {
		const state_class_map = {
			desktop: {
				empty: "hierarchy-main-empty",
				non_empty: "hierarchy-main-chart",
				remove_selectors: ["#hierarchy-chart-wrapper", ".hierarchy", "#arrows"],
			},
			mobile: {
				empty: "hierarchy-main-mobile-empty",
				non_empty: "hierarchy-main-mobile-chart",
				remove_selectors: [".hierarchy-mobile", ".sibling-group", "#arrows"],
			},
		};

		return state_class_map[device_type] || state_class_map.desktop;
	},

	apply_empty_state({ chart, company, device_type, state_config }) {
		return this.get_employee_count(company).then((employee_count) => {
			if (employee_count > 0) {
				this.clear_empty_state(chart.page);
				this.set_main_state(chart.page, state_config.non_empty);
				return false;
			}

			(state_config.remove_selectors || []).forEach((selector) => {
				chart.page.main.find(selector).remove();
			});

			this.set_main_state(chart.page, state_config.empty);
			this.render_empty_state({
				page: chart.page,
				doctype: chart.doctype,
				company,
				device_type,
			});

			return true;
		});
	},

	handle_company_change({ chart, method, device_type }) {
		const state_config = this.get_state_config(device_type);
		const company = chart.page.fields_dict.company?.get_value();

		if (!company) {
			this.clear_empty_state(chart.page);
			return Promise.resolve();
		}

		return frappe
			.call({
				method,
				args: { company },
			})
			.then((r) => {
				const has_root_nodes = Boolean(r.message && r.message.length);

				if (has_root_nodes) {
					this.clear_empty_state(chart.page);
					this.set_main_state(chart.page, state_config.non_empty);
					return;
				}

				return this.apply_empty_state({
					chart,
					company,
					device_type,
					state_config,
				});
			});
	},

	bind_empty_state_handler(chart, method, device_type) {
		chart.page.main.addClass("hierarchy-chart-main");

		if (!chart._render_root_nodes_original) {
			chart._render_root_nodes_original = chart.render_root_nodes.bind(chart);
			chart.render_root_nodes = (...args) => {
				return Promise.resolve(chart._render_root_nodes_original(...args)).then(
					(result) => {
						chart.page.main
							.find('[data-fieldname="company"] .link-field')
							.addClass("hierarchy-company-link-field");

						return Promise.resolve(
							this.handle_company_change({ chart, method, device_type }),
						).then(() => result);
					},
				);
			};
		}
	},
});

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
			const device_type = frappe.is_mobile() ? "mobile" : "desktop";

			if (frappe.is_mobile()) {
				organizational_chart = new hrms.HierarchyChartMobile("Employee", wrapper, method);
			} else {
				organizational_chart = new hrms.HierarchyChart("Employee", wrapper, method);
			}

			frappe.breadcrumbs.add("HR");
			hrms.organizational_chart.bind_empty_state_handler(
				organizational_chart,
				method,
				device_type,
			);
			organizational_chart.show();
		});
	});
};
