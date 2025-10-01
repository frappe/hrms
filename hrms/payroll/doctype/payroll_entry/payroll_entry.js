// Copyright (c) 2017, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

var in_progress = false;

frappe.provide("erpnext.accounts.dimensions");

frappe.ui.form.on("Payroll Entry", {
	onload: function (frm) {
		frm.ignore_doctypes_on_cancel_all = ["Salary Slip", "Journal Entry"];

		if (!frm.doc.posting_date) {
			frm.doc.posting_date = frappe.datetime.nowdate();
		}
		frm.toggle_reqd(["payroll_frequency"], !frm.doc.salary_slip_based_on_timesheet);

		erpnext.accounts.dimensions.setup_dimension_filters(frm, frm.doctype);
		frm.events.department_filters(frm);
		frm.events.payroll_payable_account_filters(frm);

		frappe.realtime.off("completed_salary_slip_creation");
		frappe.realtime.on("completed_salary_slip_creation", function () {
			frm.reload_doc();
		});

		frappe.realtime.off("completed_salary_slip_submission");
		frappe.realtime.on("completed_salary_slip_submission", function () {
			frm.reload_doc();
		});
	},

	department_filters: function (frm) {
		frm.set_query("department", function () {
			return {
				filters: {
					company: frm.doc.company,
				},
			};
		});
	},

	payroll_payable_account_filters: function (frm) {
		frm.set_query("payroll_payable_account", function () {
			return {
				filters: {
					company: frm.doc.company,
					root_type: "Liability",
					is_group: 0,
				},
			};
		});
	},

	refresh: function (frm) {
		if (frm.doc.status === "Queued") frm.page.btn_secondary.hide();

		if (frm.doc.docstatus === 0 && !frm.is_new()) {
			frm.page.clear_primary_action();
			frm.add_custom_button(__("Get Employees"), function () {
				frm.events.show_employee_selection_dialog(frm);
			}).toggleClass("btn-primary", !(frm.doc.employees || []).length);
		}

		if (
			(frm.doc.employees || []).length &&
			!frappe.model.has_workflow(frm.doctype) &&
			!cint(frm.doc.salary_slips_created) &&
			frm.doc.docstatus != 2
		) {
			if (frm.doc.docstatus == 0 && !frm.is_new()) {
				frm.page.clear_primary_action();
				frm.page.set_primary_action(__("Create Salary Slips"), () => {
					frm.save("Submit").then(() => {
						frm.page.clear_primary_action();
						frm.refresh();
					});
				});
			}
		}

		if (frm.doc.docstatus == 1) {
			if (frm.custom_buttons) frm.clear_custom_buttons();
			frm.events.add_context_buttons(frm);
		}

		if (frm.doc.status == "Failed" && frm.doc.error_message) {
			const issue = `<a id="jump_to_error" style="text-decoration: underline;">issue</a>`;
			let process = cint(frm.doc.salary_slips_created) ? "submission" : "creation";

			frm.dashboard.set_headline(
				__("Salary Slip {0} failed. You can resolve the {1} and retry {0}.", [
					process,
					issue,
				]),
			);

			$("#jump_to_error").on("click", (e) => {
				e.preventDefault();
				frm.scroll_to_field("error_message");
			});
		}
	},

	get_employee_details: function (frm) {
		return frappe
			.call({
				doc: frm.doc,
				method: "fill_employee_details",
				freeze: true,
				freeze_message: __("Fetching Employees"),
			})
			.then((r) => {
				if (r.docs?.[0]?.employees) {
					frm.dirty();
					frm.save();
				}

				frm.refresh();

				if (r.docs?.[0]?.validate_attendance) {
					render_employee_attendance(frm, r.message);
				}
				frm.scroll_to_field("employees");
			});
	},

	show_employee_selection_dialog: function (frm) {
		// First fetch employees with salary preview
		frappe.call({
			doc: frm.doc,
			method: "get_employees_with_salary_preview",
			freeze: true,
			freeze_message: __("Calculating Salary Preview..."),
			callback: function (r) {
				if (r.message && r.message.length > 0) {
					frm.events.render_employee_selection_dialog(frm, r.message);
				} else {
					frappe.msgprint(__("No employees found for the selected criteria"));
				}
			},
		});
	},

	render_employee_selection_dialog: function (frm, employees) {
		// Create HTML table for employee selection
		let html = `
			<div class="employee-selection-wrapper">
				<div class="row mb-3">
					<div class="col-md-6">
						<div class="checkbox">
							<label>
								<input type="checkbox" id="select-all-employees" checked>
								<span class="label-area">${__("Select All")}</span>
							</label>
						</div>
					</div>
					<div class="col-md-6 text-right">
						<strong>${__("Total")}: <span id="total-salary-amount">0</span></strong>
					</div>
				</div>
				<div class="table-responsive" style="max-height: 400px; overflow-y: auto;">
					<table class="table table-hover">
						<thead>
							<tr>
								<th width="5%">${__("Select")}</th>
								<th width="25%">${__("Employee")}</th>
								<th width="15%">${__("Designation")}</th>
								<th width="20%" class="text-right">${__("Gross Pay")}</th>
								<th width="15%" class="text-right">${__("Deductions")}</th>
								<th width="20%" class="text-right">${__("Net Pay")}</th>
							</tr>
						</thead>
						<tbody>
		`;

		let total_net_pay = 0;
		employees.forEach((emp, idx) => {
			let tooltip_content = frm.events.get_salary_component_tooltip(emp);
			let row_class = emp.error ? "text-danger" : "";
			let net_pay_value = emp.error
				? __("Error")
				: frappe.format(emp.net_pay, { fieldtype: "Currency" });

			html += `
				<tr class="employee-row ${row_class}"
					data-employee="${emp.employee}"
					data-tooltip-content='${JSON.stringify(tooltip_content)}'>
					<td>
						<input type="checkbox" class="employee-checkbox"
							value="${emp.employee}"
							${emp.error ? "disabled" : "checked"}
							data-net-pay="${emp.net_pay || 0}">
					</td>
					<td>
						<div>${emp.employee_name || ""}</div>
						<div class="text-muted small">${emp.employee}</div>
					</td>
					<td>${emp.designation || ""}</td>
					<td class="text-right salary-column" data-column="gross_pay">
						${frappe.format(emp.gross_pay, { fieldtype: "Currency" })}
					</td>
					<td class="text-right salary-column" data-column="deductions">
						${frappe.format(emp.total_deduction, { fieldtype: "Currency" })}
					</td>
					<td class="text-right salary-column" data-column="net_pay">
						<strong>${net_pay_value}</strong>
					</td>
				</tr>
			`;

			if (!emp.error) {
				total_net_pay += emp.net_pay || 0;
			}
		});

		html += `
						</tbody>
					</table>
				</div>
			</div>
		`;

		let dialog = new frappe.ui.Dialog({
			title: __("Select Employees for Payroll"),
			size: "extra-large",
			fields: [
				{
					fieldname: "employee_selection_html",
					fieldtype: "HTML",
					options: html,
				},
			],
			primary_action_label: __("Add Selected Employees"),
			primary_action: function () {
				let selected_employees = [];
				dialog.$wrapper.find(".employee-checkbox:checked").each(function () {
					selected_employees.push($(this).val());
				});

				if (selected_employees.length === 0) {
					frappe.msgprint(__("Please select at least one employee"));
					return;
				}

				dialog.hide();

				// Call the method to add selected employees
				frappe.call({
					doc: frm.doc,
					method: "fill_employee_details_selective",
					args: {
						selected_employees: selected_employees,
					},
					freeze: true,
					freeze_message: __("Adding Selected Employees..."),
					callback: function (r) {
						if (r.docs?.[0]?.employees) {
							frm.dirty();
							frm.save();
						}

						frm.refresh();

						if (r.docs?.[0]?.validate_attendance) {
							render_employee_attendance(frm, r.message);
						}
						frm.scroll_to_field("employees");

						frappe.show_alert({
							message: __("{0} employees added", [selected_employees.length]),
							indicator: "green",
						});
					},
				});
			},
		});

		dialog.show();

		// Initialize tooltips and event handlers
		frm.events.setup_employee_selection_handlers(frm, dialog, total_net_pay);
	},

	setup_employee_selection_handlers: function (frm, dialog, initial_total) {
		let $wrapper = dialog.$wrapper;

		// Update total salary display
		$wrapper
			.find("#total-salary-amount")
			.html($(frappe.format(initial_total, { fieldtype: "Currency" })).text());

		// Handle select all checkbox
		$wrapper.find("#select-all-employees").on("change", function () {
			let checked = $(this).prop("checked");
			$wrapper.find(".employee-checkbox:not(:disabled)").prop("checked", checked);
			frm.events.update_total_salary(frm, dialog);
		});

		// Handle individual checkbox changes
		$wrapper.find(".employee-checkbox").on("change", function () {
			frm.events.update_total_salary(frm, dialog);

			// Update select all checkbox state
			let all_checked =
				$wrapper.find(".employee-checkbox:not(:disabled)").length ===
				$wrapper.find(".employee-checkbox:not(:disabled):checked").length;
			$wrapper.find("#select-all-employees").prop("checked", all_checked);
		});

		// Setup tooltips on salary columns hover
		$wrapper.find(".salary-column").on("mouseenter", function (e) {
			let $row = $(this).closest(".employee-row");
			let tooltip_content = $row.data("tooltip-content");
			if (!tooltip_content || tooltip_content.error) return;

			let tooltip_html = frm.events.format_tooltip_content(tooltip_content);

			// Create tooltip element
			let $tooltip = $(`
				<div class="salary-tooltip" style="
					position: absolute;
					z-index: 10000;
					background: white;
					border: 1px solid #d1d8dd;
					border-radius: 4px;
					padding: 10px;
					box-shadow: 0 2px 6px rgba(0,0,0,0.1);
					max-width: 400px;
				">
					${tooltip_html}
				</div>
			`);

			// Position and show tooltip
			$("body").append($tooltip);
			$tooltip.css({
				top: e.pageY + 10,
				left: e.pageX + 10,
			});

			// Store tooltip reference on the cell
			$(this).data("tooltip", $tooltip);
		});

		$wrapper.find(".salary-column").on("mouseleave", function () {
			let $tooltip = $(this).data("tooltip");
			if ($tooltip) {
				$tooltip.remove();
				$(this).removeData("tooltip");
			}
		});

		// Update tooltip position on mouse move within salary columns
		$wrapper.find(".salary-column").on("mousemove", function (e) {
			let $tooltip = $(this).data("tooltip");
			if ($tooltip) {
				$tooltip.css({
					top: e.pageY + 10,
					left: e.pageX + 10,
				});
			}
		});
	},

	update_total_salary: function (frm, dialog) {
		let total = 0;
		dialog.$wrapper.find(".employee-checkbox:checked").each(function () {
			total += parseFloat($(this).data("net-pay") || 0);
		});
		dialog.$wrapper
			.find("#total-salary-amount")
			.html(frappe.format(total, { fieldtype: "Currency" }));
	},

	get_salary_component_tooltip: function (emp) {
		if (emp.error) {
			return { error: true };
		}

		return {
			employee: emp.employee,
			employee_name: emp.employee_name,
			payment_days: emp.payment_days,
			working_days: emp.working_days,
			earnings: emp.earnings || [],
			deductions: emp.deductions || [],
			gross_pay: emp.gross_pay,
			total_deduction: emp.total_deduction,
			net_pay: emp.net_pay,
		};
	},

	format_tooltip_content: function (data) {
		let html = `
			<div style="font-size: 12px;">
				<h6 style="margin-bottom: 10px; font-weight: bold;">
					${data.employee} - ${data.employee_name}
				</h6>
				<div style="margin-bottom: 8px;">
					<small class="text-muted">${__("Payment Days")}: ${data.payment_days} / ${data.working_days}</small>
				</div>
		`;

		if (data.earnings && data.earnings.length > 0) {
			html += `
				<div style="margin-bottom: 8px;">
					<strong style="color: #5e64ff;">${__("Earnings")}:</strong>
					<table style="width: 100%; margin-top: 5px;">
			`;
			data.earnings.forEach((earning) => {
				html += `
					<tr>
						<td style="padding: 2px 0;">${earning.salary_component}</td>
						<td style="text-align: right; padding: 2px 0;">
							${frappe.format(earning.amount, { fieldtype: "Currency" })}
						</td>
					</tr>
				`;
			});
			html += `
					</table>
				</div>
			`;
		}

		if (data.deductions && data.deductions.length > 0) {
			html += `
				<div style="margin-bottom: 8px;">
					<strong style="color: #ff5858;">${__("Deductions")}:</strong>
					<table style="width: 100%; margin-top: 5px;">
			`;
			data.deductions.forEach((deduction) => {
				html += `
					<tr>
						<td style="padding: 2px 0;">${deduction.salary_component}</td>
						<td style="text-align: right; padding: 2px 0;">
							${frappe.format(deduction.amount, { fieldtype: "Currency" })}
						</td>
					</tr>
				`;
			});
			html += `
					</table>
				</div>
			`;
		}

		html += `
			<div style="border-top: 1px solid #d1d8dd; padding-top: 8px; margin-top: 8px;">
				<table style="width: 100%;">
					<tr>
						<td><strong>${__("Gross Pay")}:</strong></td>
						<td style="text-align: right;">
							${frappe.format(data.gross_pay, { fieldtype: "Currency" })}
						</td>
					</tr>
					<tr>
						<td><strong>${__("Total Deductions")}:</strong></td>
						<td style="text-align: right;">
							${frappe.format(data.total_deduction, { fieldtype: "Currency" })}
						</td>
					</tr>
					<tr style="font-size: 13px;">
						<td><strong>${__("Net Pay")}:</strong></td>
						<td style="text-align: right;">
							<strong>${frappe.format(data.net_pay, { fieldtype: "Currency" })}</strong>
						</td>
					</tr>
				</table>
			</div>
		</div>
		`;

		return html;
	},

	create_salary_slip: function (frm) {
		frappe.call({
			method: "run_doc_method",
			args: {
				method: "create_salary_slips",
				dt: "Payroll Entry",
				dn: frm.doc.name,
			},
		});
	},

	add_context_buttons: function (frm) {
		if (
			frm.doc.salary_slips_submitted ||
			(frm.doc.__onload && frm.doc.__onload.submitted_ss)
		) {
			frm.events.add_bank_entry_button(frm);
		} else if (frm.doc.salary_slips_created && frm.doc.status !== "Queued") {
			frm.add_custom_button(__("Submit Salary Slip"), function () {
				submit_salary_slip(frm);
			}).addClass("btn-primary");
		} else if (!frm.doc.salary_slips_created && frm.doc.status === "Failed") {
			frm.add_custom_button(__("Create Salary Slips"), function () {
				frm.trigger("create_salary_slip");
			}).addClass("btn-primary");
		}
	},

	add_bank_entry_button: function (frm) {
		frm.call("has_bank_entries").then((r) => {
			if (!r.message.has_bank_entries) {
				frm.add_custom_button(__("Make Bank Entry"), function () {
					make_bank_entry(frm);
				}).addClass("btn-primary");
			} else if (!r.message.has_bank_entries_for_withheld_salaries) {
				frm.add_custom_button(__("Release Withheld Salaries"), function () {
					make_bank_entry(frm, (for_withheld_salaries = 1));
				}).addClass("btn-primary");
			}
		});
	},

	setup: function (frm) {
		frm.add_fetch("company", "cost_center", "cost_center");

		frm.set_query("payment_account", function () {
			var account_types = ["Bank", "Cash"];
			return {
				filters: {
					account_type: ["in", account_types],
					is_group: 0,
					company: frm.doc.company,
				},
			};
		});

		frm.set_query("employee", "employees", () => {
			let error_fields = [];
			let mandatory_fields = ["company", "payroll_frequency", "start_date", "end_date"];

			let message = __("Mandatory fields required in {0}", [__(frm.doc.doctype)]);

			mandatory_fields.forEach((field) => {
				if (!frm.doc[field]) {
					error_fields.push(frappe.unscrub(field));
				}
			});

			if (error_fields && error_fields.length) {
				message = message + "<br><br><ul><li>" + error_fields.join("</li><li>") + "</ul>";
				frappe.throw({
					message: message,
					indicator: "red",
					title: __("Missing Fields"),
				});
			}

			return {
				query: "hrms.payroll.doctype.payroll_entry.payroll_entry.employee_query",
				filters: frm.events.get_employee_filters(frm),
			};
		});
	},

	get_employee_filters: function (frm) {
		let filters = {};

		let fields = [
			"company",
			"start_date",
			"end_date",
			"payroll_frequency",
			"payroll_payable_account",
			"currency",
			"department",
			"branch",
			"designation",
			"salary_slip_based_on_timesheet",
			"grade",
		];

		fields.forEach((field) => {
			if (frm.doc[field] || frm.doc[field] === 0) {
				filters[field] = frm.doc[field];
			}
		});

		if (frm.doc.employees) {
			let employees = frm.doc.employees.filter((d) => d.employee).map((d) => d.employee);
			if (employees && employees.length) {
				filters["employees"] = employees;
			}
		}
		return filters;
	},

	payroll_frequency: function (frm) {
		frm.trigger("set_start_end_dates").then(() => {
			frm.events.clear_employee_table(frm);
		});
	},

	company: function (frm) {
		frm.events.clear_employee_table(frm);
		erpnext.accounts.dimensions.update_dimension(frm, frm.doctype);
		frm.trigger("set_payable_account_and_currency");
	},

	set_payable_account_and_currency: function (frm) {
		frappe.db.get_value("Company", { name: frm.doc.company }, "default_currency", (r) => {
			frm.set_value("currency", r.default_currency);
		});
		frappe.db.get_value(
			"Company",
			{ name: frm.doc.company },
			"default_payroll_payable_account",
			(r) => {
				frm.set_value("payroll_payable_account", r.default_payroll_payable_account);
			},
		);
	},

	currency: function (frm) {
		var company_currency;
		if (!frm.doc.company) {
			company_currency = erpnext.get_currency(frappe.defaults.get_default("Company"));
		} else {
			company_currency = erpnext.get_currency(frm.doc.company);
		}
		if (frm.doc.currency) {
			if (company_currency != frm.doc.currency) {
				frappe.call({
					method: "erpnext.setup.utils.get_exchange_rate",
					args: {
						from_currency: frm.doc.currency,
						to_currency: company_currency,
					},
					callback: function (r) {
						frm.set_value("exchange_rate", flt(r.message));
						frm.set_df_property("exchange_rate", "hidden", 0);
						frm.set_df_property(
							"exchange_rate",
							"description",
							"1 " + frm.doc.currency + " = [?] " + company_currency,
						);
					},
				});
			} else {
				frm.set_value("exchange_rate", 1.0);
				frm.set_df_property("exchange_rate", "hidden", 1);
				frm.set_df_property("exchange_rate", "description", "");
			}
		}
	},

	department: function (frm) {
		frm.events.clear_employee_table(frm);
	},
	grade: function (frm) {
		frm.events.clear_employee_table(frm);
	},
	designation: function (frm) {
		frm.events.clear_employee_table(frm);
	},

	branch: function (frm) {
		frm.events.clear_employee_table(frm);
	},

	start_date: function (frm) {
		if (!in_progress && frm.doc.start_date) {
			frm.trigger("set_end_date");
		} else {
			// reset flag
			in_progress = false;
		}
		frm.events.clear_employee_table(frm);
	},

	project: function (frm) {
		frm.events.clear_employee_table(frm);
	},

	salary_slip_based_on_timesheet: function (frm) {
		frm.toggle_reqd(["payroll_frequency"], !frm.doc.salary_slip_based_on_timesheet);
	},

	set_start_end_dates: function (frm) {
		if (frm.doc.payroll_frequency) {
			frappe.call({
				method: "hrms.payroll.doctype.payroll_entry.payroll_entry.get_start_end_dates",
				args: {
					payroll_frequency: frm.doc.payroll_frequency,
					start_date: frm.doc.posting_date,
				},
				callback: function (r) {
					if (r.message) {
						in_progress = true;
						frm.set_value("start_date", r.message.start_date);
						frm.set_value("end_date", r.message.end_date);
					}
				},
			});
		}
	},

	set_end_date: function (frm) {
		frappe.call({
			method: "hrms.payroll.doctype.payroll_entry.payroll_entry.get_end_date",
			args: {
				frequency: frm.doc.payroll_frequency,
				start_date: frm.doc.start_date,
			},
			callback: function (r) {
				if (r.message) {
					frm.set_value("end_date", r.message.end_date);
				}
			},
		});
	},

	validate_attendance: function (frm) {
		if (frm.doc.validate_attendance && frm.doc.employees?.length > 0) {
			frappe.call({
				method: "get_employees_with_unmarked_attendance",
				args: {},
				callback: function (r) {
					render_employee_attendance(frm, r.message);
				},
				doc: frm.doc,
				freeze: true,
				freeze_message: __("Validating Employee Attendance..."),
			});
		} else {
			frm.fields_dict.attendance_detail_html.html("");
		}
	},

	clear_employee_table: function (frm) {
		frm.clear_table("employees");
		frm.refresh();
	},
});

// Submit salary slips

const submit_salary_slip = function (frm) {
	frappe.confirm(
		__(
			"This will submit Salary Slips and create accrual Journal Entry. Do you want to proceed?",
		),
		function () {
			frappe.call({
				method: "submit_salary_slips",
				args: {},
				doc: frm.doc,
				freeze: true,
				freeze_message: __("Submitting Salary Slips and creating Journal Entry..."),
			});
		},
		function () {
			if (frappe.dom.freeze_count) {
				frappe.dom.unfreeze();
			}
		},
	);
};

let make_bank_entry = function (frm, for_withheld_salaries = 0) {
	const doc = frm.doc;
	if (doc.payment_account) {
		return frappe.call({
			method: "run_doc_method",
			args: {
				method: "make_bank_entry",
				dt: "Payroll Entry",
				dn: frm.doc.name,
				args: { for_withheld_salaries: for_withheld_salaries },
			},
			callback: function () {
				frappe.set_route("List", "Journal Entry", {
					"Journal Entry Account.reference_name": frm.doc.name,
				});
			},
			freeze: true,
			freeze_message: __("Creating Payment Entries......"),
		});
	} else {
		frappe.msgprint(__("Payment Account is mandatory"));
		frm.scroll_to_field("payment_account");
	}
};

let render_employee_attendance = function (frm, data) {
	frm.fields_dict.attendance_detail_html.html(
		frappe.render_template("employees_with_unmarked_attendance", {
			data: data,
		}),
	);
};
