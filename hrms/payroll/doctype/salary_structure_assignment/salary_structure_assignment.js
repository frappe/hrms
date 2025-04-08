// Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Salary Structure Assignment", {
	setup: function (frm) {
		frm.set_query("employee", function () {
			return {
				query: "erpnext.controllers.queries.employee_query",
				filters: { company: frm.doc.company },
			};
		});
		frm.set_query("salary_structure", function () {
			return {
				filters: {
					company: frm.doc.company,
					docstatus: 1,
					is_active: "Yes",
				},
			};
		});

		frm.set_query("income_tax_slab", function () {
			return {
				filters: {
					company: frm.doc.company,
					docstatus: 1,
					disabled: 0,
					currency: frm.doc.currency,
				},
			};
		});

		frm.set_query("payroll_payable_account", function () {
			var company_currency = erpnext.get_currency(frm.doc.company);
			return {
				filters: {
					company: frm.doc.company,
					root_type: "Liability",
					is_group: 0,
					account_currency: ["in", [frm.doc.currency, company_currency]],
				},
			};
		});

		frm.set_query("cost_center", "payroll_cost_centers", function () {
			return {
				filters: {
					company: frm.doc.company,
					is_group: 0,
				},
			};
		});
	},

	refresh: function (frm) {
		frm.trigger("ctc_preview");
		frm.trigger("toggle_opening_balances_section");

		if (frm.doc.docstatus != 1) return;

		frm.add_custom_button(
			__("Payroll Entry"),
			() => {
				frappe.model.with_doctype("Payroll Entry", () => {
					const doc = frappe.model.get_new_doc("Payroll Entry");
					frappe.set_route("Form", "Payroll Entry", doc.name);
				});
			},
			__("Create"),
		);
		frm.page.set_inner_btn_group_as_primary(__("Create"));

		frm.add_custom_button(
			__("Preview Salary Slip"),
			function () {
				frm.trigger("preview_salary_slip");
			},
			__("Actions"),
		);

		

		
	},

	ctc_preview: function (frm) {
		if (frm.doc.docstatus !== 1) return;
	
		let total_monthly = 0;
		let total_annual = 0;
	
		const formatRow = (component, monthly) => {
			const annual = monthly * 12;
			total_monthly += monthly;
			total_annual += annual;
			return `
				<tr>
					<td>${component}</td>
					<td>${format_currency(monthly)}</td>
					<td>${format_currency(annual)}</td>
				</tr>
			`;
		};
	
		const fetchCTCRows = (components) => {
			return Promise.all(components.map(item => {
				return new Promise(resolve => {
					frappe.call({
						method: "frappe.client.get",
						args: {
							doctype: "Salary Component",
							name: item.salary_component
						},
						callback: function (res) {
							if (res.message && res.message.is_part_of_ctc === 1) {
								resolve(formatRow(item.salary_component, item.amount));
							} else {
								resolve('');
							}
						}
					});
				});
			}));
		};
	
		frappe.call({
			method: "hrms.payroll.doctype.salary_structure.salary_structure.make_salary_slip",
			args: {
				source_name: frm.doc.salary_structure,
				employee: frm.doc.employee,
				print_format: 'Salary Slip Standard',
				posting_date: frm.doc.from_date,
				for_preview: 1,
			},
			callback: async function (response) {
				if (!response.message) return;
	
				const earnings = response.message.earnings || [];
				const deductions = response.message.deductions || [];
	
				const [earnings_rows, deductions_rows] = await Promise.all([
					fetchCTCRows(earnings),
					fetchCTCRows(deductions)
				]);
	
				const earnings_html = earnings_rows.join('');
				const deductions_html = deductions_rows.join('');
	
				const final_html = `
					<table style="width:100%; border-collapse: collapse; margin-bottom: 20px;" border="1">
					  <thead>
						<tr>
						  <th style="width:50%;">Salary Component (Earnings)</th>
						  <th style="width:25%;">Monthly Amount</th>
						  <th style="width:25%;">Annual Amount</th>
						</tr>
					  </thead>
					  <tbody>
						${earnings_html}
					  </tbody>
					</table>
	
					<table style="width:100%; border-collapse: collapse; margin-bottom: 20px;" border="1">
					  <thead>
						<tr>
						  <th style="width:50%;">Salary Component (Deductions)</th>
						  <th style="width:25%;">Monthly Amount</th>
						  <th style="width:25%;">Annual Amount</th>
						</tr>
					  </thead>
					  <tbody>
						${deductions_html}
					  </tbody>
					</table>
	
					<table style="width:100%; border-collapse: collapse;" border="1">
					  <tbody>
						<tr>
							<td style="width:50%;"><b>Total CTC</b></td>
							<td style="width:25%;"><b>${format_currency(total_monthly)}</b></td>
							<td style="width:25%;"><b>${format_currency(total_annual)}</b></td>
						</tr>
					  </tbody>
					</table>
				`;
	
				frm.fields_dict.ctc_breakup.$wrapper.html(final_html);
			}
		});
	},
	

	employee: function (frm) {
		if (frm.doc.employee) {
			frm.trigger("set_payroll_cost_centers");
			frm.trigger("toggle_opening_balances_section");
		} else {
			frm.set_value("payroll_cost_centers", []);
		}
	},

	company: function (frm) {
		if (frm.doc.company) {
			frappe.db.get_value(
				"Company",
				frm.doc.company,
				"default_payroll_payable_account",
				(r) => {
					frm.set_value("payroll_payable_account", r.default_payroll_payable_account);
				},
			);
		}
	},

	preview_salary_slip: function (frm) {
		frappe.db.get_value(
			"Salary Structure",
			frm.doc.salary_structure,
			"salary_slip_based_on_timesheet",
			(r) => {
				const print_format = r.salary_slip_based_on_timesheet
					? "Salary Slip based on Timesheet"
					: "Salary Slip Standard";
				frappe.call({
					method: "hrms.payroll.doctype.salary_structure.salary_structure.make_salary_slip",
					args: {
						source_name: frm.doc.salary_structure,
						employee: frm.doc.employee,
						posting_date: frm.doc.from_date,
						as_print: 1,
						print_format: print_format,
						for_preview: 1,
					},
					callback: function (r) {
						const new_window = window.open();
						new_window.document.write(r.message);
					},
				});
			},
		);
	},

	set_payroll_cost_centers: function (frm) {
		if (frm.doc.payroll_cost_centers && frm.doc.payroll_cost_centers.length < 1) {
			frappe.call({
				method: "set_payroll_cost_centers",
				doc: frm.doc,
				callback: function (data) {
					refresh_field("payroll_cost_centers");
				},
			});
		}
	},

	toggle_opening_balances_section: function (frm) {
		if (!frm.doc.from_date || !frm.doc.employee) return;

		frm.call("are_opening_entries_required").then((data) => {
			if (data.message) {
				frm.set_df_property("opening_balances_section", "hidden", 0);
			} else {
				frm.set_df_property("opening_balances_section", "hidden", 1);
			}
		});
	},

	from_date: function (frm) {
		if (frm.doc.from_date) {
			frm.trigger("toggle_opening_balances_section");
		}
	},
});
