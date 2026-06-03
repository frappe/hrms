// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

const HIDDEN_QUICK_ENTRY_FIELDS = ["status", "posting_date", "naming_series"];

function set_hidden_defaults(quick_entry) {
	quick_entry.doc.status = quick_entry.doc.status || "Open";
	quick_entry.doc.posting_date = quick_entry.doc.posting_date || frappe.datetime.get_today();

	const naming_series_field = quick_entry.get_field("naming_series");
	const default_series =
		naming_series_field?.df.default || naming_series_field?.df.options?.split("\n")[0];

	if (default_series) {
		quick_entry.doc.naming_series = quick_entry.doc.naming_series || default_series;
	}
}

function hide_field_completely(quick_entry, fieldname) {
	quick_entry.set_df_property(fieldname, "hidden", 1);
	quick_entry.get_field(fieldname)?.$wrapper?.hide();
}

function get_extra_fields_container(quick_entry) {
	if (!quick_entry._extra_fields_container) {
		quick_entry._extra_fields_container = $(
			"<div class='leave-calendar-extra-fields mt-2'></div>",
		);
		const anchor = quick_entry._date_fields_row || quick_entry.get_field("to_date")?.$wrapper;

		if (anchor?.after) {
			anchor.after(quick_entry._extra_fields_container);
		} else {
			quick_entry.$body?.find(".form-layout")?.append(quick_entry._extra_fields_container);
		}
	}

	return quick_entry._extra_fields_container;
}

function ensure_reason_field(quick_entry) {
	const extra_fields_container = get_extra_fields_container(quick_entry);
	const reason_df = frappe.meta.get_docfield("Leave Application", "description");
	if (reason_df && extra_fields_container?.get?.(0)) {
		quick_entry._reason_control = frappe.ui.form.make_control({
			df: {
				...reason_df,
				label: __("Reason"),
				hidden: 0,
				reqd: 0,
				placeholder: __("Provide a short reason for leave."),
			},
			parent: extra_fields_container.get(0),
			render_input: true,
			doc: quick_entry.dialog.doc,
		});

		quick_entry._reason_control?.$wrapper?.addClass("mt-2");
		quick_entry._reason_control?.$input?.on("input change", () => {
			const value = quick_entry._reason_control?.get_value?.() || "";
			quick_entry.doc.description = value;
			quick_entry.dialog.doc.description = value;
		});
	}

	if (quick_entry._reason_control?.$wrapper) {
		extra_fields_container?.append(quick_entry._reason_control.$wrapper);
	}

	const value = quick_entry.doc.description || quick_entry.dialog.doc.description || "";
	quick_entry._reason_control?.set_value?.(value, true);
	quick_entry.doc.description = value;
	quick_entry.dialog.doc.description = value;
}

function sync_reason_value(quick_entry) {
	const raw_value = quick_entry._reason_control?.get_value?.();
	const value =
		raw_value !== undefined && raw_value !== null
			? raw_value
			: quick_entry.dialog.get_value("description") || quick_entry.doc.description || "";

	quick_entry.doc.description = value;
	quick_entry.dialog.doc.description = value;

	return value;
}

function ensure_total_leave_days_display(quick_entry) {
	if (quick_entry._total_leave_days_control) {
		return;
	}
	const extra_fields_container = get_extra_fields_container(quick_entry);
	const total_leave_days_df = frappe.meta.get_docfield("Leave Application", "total_leave_days");
	if (!total_leave_days_df || !extra_fields_container?.get?.(0)) {
		return;
	}

	const control = frappe.ui.form.make_control({
		df: {
			...total_leave_days_df,
			hidden: 0,
			read_only: 1,
			reqd: 0,
		},
		parent: extra_fields_container.get(0),
		render_input: true,
		doc: quick_entry.dialog.doc,
	});

	control?.toggle_description?.(false);
	control?.$wrapper?.addClass("mt-2");
	extra_fields_container.prepend(control.$wrapper);
	quick_entry._total_leave_days_control = control;
}

function set_total_leave_days_value(quick_entry, value) {
	const has_value = value !== "" && value !== null && value !== undefined;
	const numeric_value = has_value ? Number(value) : "";

	if (quick_entry._total_leave_days_control?.set_value) {
		quick_entry._total_leave_days_control.set_value(numeric_value, true);
	} else {
		quick_entry.set_value("total_leave_days", numeric_value);
	}

	quick_entry.doc.total_leave_days = has_value ? numeric_value : 0;
	quick_entry.dialog.doc.total_leave_days = has_value ? numeric_value : 0;
}

function get_quick_entry_value(quick_entry, fieldname) {
	const field = quick_entry.get_field(fieldname);
	const value = quick_entry.dialog.get_value(fieldname);

	if (field && value !== undefined && value !== null) {
		return value;
	}

	if (value !== undefined && value !== null && value !== "") {
		return value;
	}

	return quick_entry.doc[fieldname];
}

function set_leave_type_summary(quick_entry, summary) {
	const leave_type_wrapper = quick_entry.get_field("leave_type")?.$wrapper;
	if (!leave_type_wrapper) {
		return;
	}

	if (!quick_entry._leave_type_summary) {
		quick_entry._leave_type_summary = $("<div class='mt-2 mb-3'></div>");
		leave_type_wrapper.after(quick_entry._leave_type_summary);
	}

	if (!summary) {
		quick_entry._leave_type_summary.hide().text("");
		return;
	}

	if (typeof summary === "string") {
		const text = (summary || "").trim();
		if (!text) {
			quick_entry._leave_type_summary.hide().text("");
			return;
		}

		quick_entry._leave_type_summary
			.html(`<div class="small text-muted">${frappe.utils.escape_html(text)}</div>`)
			.show();
		return;
	}

	const allocated = frappe.utils.escape_html(summary.allocated || "0.0");
	const used = frappe.utils.escape_html(summary.used || "0.0");
	const remaining = frappe.utils.escape_html(summary.remaining || "0.0");

	quick_entry._leave_type_summary
		.html(
			frappe.render_template("leave_application_calendar_summary", {
				allocated,
				used,
				remaining,
			}),
		)
		.show();
}

function setup_date_fields_row(quick_entry) {
	const from_date_field = quick_entry.get_field("from_date");
	const to_date_field = quick_entry.get_field("to_date");

	if (
		!from_date_field?.$wrapper ||
		!to_date_field?.$wrapper ||
		quick_entry._date_row_setup_done
	) {
		return;
	}

	const row = $("<div class='row'></div>");
	from_date_field.$wrapper.before(row);
	row.append(from_date_field.$wrapper);
	row.append(to_date_field.$wrapper);

	from_date_field.$wrapper.addClass("col-sm-6 pr-1");
	to_date_field.$wrapper.addClass("col-sm-6 pl-1");

	quick_entry._date_row_setup_done = true;
	quick_entry._date_fields_row = row;
}

function set_allowed_leave_types_query(quick_entry, allowed_leave_types) {
	const allowed = Array.from(new Set((allowed_leave_types || []).filter(Boolean)));
	quick_entry._allowed_leave_types = allowed;

	quick_entry.set_query("leave_type", () => {
		return {
			filters: [
				[
					"leave_type_name",
					"in",
					quick_entry._allowed_leave_types?.length
						? quick_entry._allowed_leave_types
						: ["__no_allowed_leave_type__"],
				],
			],
		};
	});
}

function refresh_allowed_leave_types(quick_entry) {
	const employee = get_quick_entry_value(quick_entry, "employee");
	const date =
		get_quick_entry_value(quick_entry, "from_date") ||
		quick_entry.doc.posting_date ||
		frappe.datetime.get_today();

	if (!employee) {
		set_allowed_leave_types_query(quick_entry, []);
		return Promise.resolve();
	}

	const request_id = (quick_entry._leave_type_filter_request_id || 0) + 1;
	quick_entry._leave_type_filter_request_id = request_id;

	return frappe
		.call({
			method: "hrms.hr.doctype.leave_application.leave_application.get_leave_details",
			args: {
				employee,
				date,
			},
		})
		.then((r) => {
			if (quick_entry._leave_type_filter_request_id !== request_id) {
				return;
			}

			const leave_allocation = r?.message?.leave_allocation || {};
			const lwps = r?.message?.lwps || [];
			const allowed_leave_types = Object.keys(leave_allocation).concat(lwps);

			set_allowed_leave_types_query(quick_entry, allowed_leave_types);

			const current_leave_type = get_quick_entry_value(quick_entry, "leave_type");
			if (current_leave_type && !allowed_leave_types.includes(current_leave_type)) {
				quick_entry.set_value("leave_type", "");
			}
		})
		.catch(() => {
			if (quick_entry._leave_type_filter_request_id !== request_id) {
				return;
			}

			set_allowed_leave_types_query(quick_entry, []);
		});
}

function format_metric(value) {
	return `${value ?? 0}`;
}

function refresh_leave_metrics(quick_entry) {
	const employee = get_quick_entry_value(quick_entry, "employee");
	const leave_type = get_quick_entry_value(quick_entry, "leave_type");
	const from_date = get_quick_entry_value(quick_entry, "from_date");
	const to_date = get_quick_entry_value(quick_entry, "to_date");
	ensure_total_leave_days_display(quick_entry);

	if (!employee || !leave_type || !from_date || !to_date) {
		quick_entry.set_intro("");
		set_total_leave_days_value(quick_entry, "");
		set_leave_type_summary(quick_entry, "");
		return;
	}

	const request_id = (quick_entry._leave_metrics_request_id || 0) + 1;
	quick_entry._leave_metrics_request_id = request_id;

	frappe
		.call({
			method: "hrms.hr.doctype.leave_application.leave_application.get_leave_metrics_and_details",
			args: {
				employee,
				leave_type,
				from_date,
				to_date,
			},
		})
		.then((response) => {
			if (quick_entry._leave_metrics_request_id !== request_id) {
				return;
			}

			const requested_days = response?.message?.number_of_leave_days;
			const allocation = response?.message?.leave_allocation?.[leave_type] || {};
			const allocated = format_metric(allocation?.total_leaves);
			const used = format_metric(allocation?.leaves_taken);
			const remaining = format_metric(allocation?.remaining_leaves);
			const has_allocation = Object.prototype.hasOwnProperty.call(
				response?.message?.leave_allocation || {},
				leave_type,
			);

			set_leave_type_summary(
				quick_entry,
				has_allocation
					? {
							allocated,
							used,
							remaining,
					  }
					: "",
			);
			set_total_leave_days_value(quick_entry, requested_days);
			quick_entry.set_intro("");
		})
		.catch(() => {
			if (quick_entry._leave_metrics_request_id !== request_id) {
				return;
			}

			quick_entry.set_intro("");
			set_total_leave_days_value(quick_entry, "");
			set_leave_type_summary(
				quick_entry,
				__("Unable to load leave allocation details right now."),
			);
		});
}

function bind_link_change(quick_entry, fieldname, handler) {
	const field = quick_entry.get_field(fieldname);
	if (!field) {
		return;
	}

	const namespaced_events = ".leave_calendar_quick_entry_link";
	const trigger_handler = frappe.utils.debounce(() => handler(), 150);

	field.$input?.off(namespaced_events);
	field.$input?.on(
		`change${namespaced_events} awesomplete-selectcomplete${namespaced_events}`,
		trigger_handler,
	);

	field.$wrapper?.off(namespaced_events);
	field.$wrapper?.on(
		`change${namespaced_events} awesomplete-selectcomplete${namespaced_events}`,
		"input, .awesomplete input",
		trigger_handler,
	);
}

function bind_input_change(quick_entry, fieldname, handler) {
	const field = quick_entry.get_field(fieldname);
	if (!field) {
		return;
	}

	const namespaced_events = ".leave_calendar_quick_entry";
	const trigger_handler = frappe.utils.debounce(() => handler(), 150);

	field.$input?.off(namespaced_events);
	field.$input?.on(
		`change${namespaced_events} input${namespaced_events} blur${namespaced_events} awesomplete-selectcomplete${namespaced_events}`,
		trigger_handler,
	);

	field.$wrapper?.off(namespaced_events);
	field.$wrapper?.on(
		`change${namespaced_events} awesomplete-selectcomplete${namespaced_events}`,
		"input, .awesomplete input",
		trigger_handler,
	);
}

function set_leave_approver_value(quick_entry, leave_approver) {
	const value = leave_approver || "";
	quick_entry.dialog.doc.leave_approver = value;
	quick_entry.doc.leave_approver = value;
	quick_entry.set_value("leave_approver", value);
	return value;
}

function get_quick_entry_employee(quick_entry) {
	return (
		quick_entry.dialog.doc.employee ||
		quick_entry.doc.employee ||
		quick_entry.dialog.get_value("employee")
	);
}

function setup_full_form_action(quick_entry) {
	quick_entry.set_secondary_action_label(__("Open Full Form"));
	quick_entry.set_secondary_action(async () => {
		sync_reason_value(quick_entry);

		const employee = get_quick_entry_employee(quick_entry);
		await sync_leave_approver(quick_entry, employee, { clear_existing: true }).catch(() => {});

		quick_entry.open_doc(true);
	});
}

function sync_leave_approver(quick_entry, employee, options = {}) {
	const { clear_existing = false } = options;
	const request_id = (quick_entry._leaveApproverRequestId || 0) + 1;
	quick_entry._leaveApproverRequestId = request_id;
	const is_latest_request = () => quick_entry._leaveApproverRequestId === request_id;

	if (clear_existing) {
		set_leave_approver_value(quick_entry, "");
	}

	return frappe
		.call({
			method: "hrms.hr.doctype.leave_application.leave_application.get_leave_approver_and_mandatory",
			args: {
				employee,
			},
		})
		.then((response) => {
			if (!is_latest_request()) {
				return;
			}

			const { is_mandatory, leave_approver } = response?.message || {};

			if (!employee) {
				if (!is_latest_request()) {
					return;
				}

				set_leave_approver_value(quick_entry, "");
				return { is_mandatory: Number(is_mandatory) || 0, leave_approver: "" };
			}

			const leave_approver_value = set_leave_approver_value(
				quick_entry,
				leave_approver || "",
			);
			return {
				is_mandatory: Number(is_mandatory) || 0,
				leave_approver: leave_approver_value,
			};
		})
		.then((result) => {
			if (result) {
				return result;
			}

			return { is_mandatory: 0, leave_approver: "" };
		});
}

function ensure_leave_approver(quick_entry, employee, options = {}) {
	const { clear_existing = false, enforce_mandatory = false } = options;

	return sync_leave_approver(quick_entry, employee, { clear_existing }).then(
		({ is_mandatory, leave_approver }) => {
			if (enforce_mandatory && is_mandatory && !leave_approver) {
				if (!employee) {
					frappe.throw({
						title: __("Employee Required"),
						message: __("Please select an Employee before continuing."),
					});
				}

				frappe.throw({
					title: __("Leave Approver Missing"),
					message: __("Please set Leave Approver for the Employee: {0}", [employee]),
				});
			}

			return leave_approver;
		},
	);
}

frappe.views.calendar["Leave Application"] = {
	field_map: {
		start: "from_date",
		end: "to_date",
		id: "name",
		title: "title",
		docstatus: 1,
		color: "color",
	},
	options: {
		header: {
			left: "prev,next today",
			center: "title",
			right: "month",
		},
		dateClick: function (info) {
			info.jsEvent?.preventDefault?.();
			info.jsEvent?.stopPropagation?.();
			return false;
		},
		select: async function (info) {
			if (info.view.type !== "dayGridMonth") {
				return;
			}

			const from_date = frappe.datetime.get_datetime_as_string(info.start).split(" ")[0];
			const to_date = frappe.datetime
				.get_datetime_as_string(new Date(info.end.getTime() - 1000))
				.split(" ")[0];

			const doc = frappe.model.get_new_doc("Leave Application");
			doc.from_date = from_date;
			doc.to_date = to_date;
			doc.employee =
				(await hrms.get_current_employee()) ||
				frappe.defaults.get_user_default("employee");

			const can_change_employee = frappe.user.has_role([
				"Administrator",
				"System Manager",
				"HR Manager",
				"HR User",
			]);

			frappe.ui.form.make_quick_entry(
				"Leave Application",
				() => {
					if (typeof cur_list !== "undefined" && cur_list.refresh) {
						cur_list.refresh();
					} else if (typeof cur_view !== "undefined" && cur_view.refresh) {
						cur_view.refresh();
					}
				},
				(quick_entry) => {
					set_hidden_defaults(quick_entry);
					setup_full_form_action(quick_entry);
					setup_date_fields_row(quick_entry);
					quick_entry.set_df_property("leave_type", "description", "");
					ensure_total_leave_days_display(quick_entry);
					ensure_reason_field(quick_entry);

					quick_entry.insert = function () {
						return new Promise((resolve, reject) => {
							sync_reason_value(quick_entry);

							quick_entry.update_doc();
							const employee = get_quick_entry_employee(quick_entry);

							ensure_leave_approver(quick_entry, employee, {
								clear_existing: true,
								enforce_mandatory: true,
							})
								.then(() => {
									quick_entry.update_doc();

									frappe.call({
										method: "frappe.client.save",
										args: { doc: quick_entry.dialog.doc },
										callback: function (r) {
											if (!r.exc) {
												quick_entry.process_after_insert(r);
												resolve(quick_entry.dialog.doc);
											} else {
												reject();
											}
										},
										error: function () {
											reject();
										},
										always: function () {
											quick_entry.dialog.working = false;
										},
									});
								})
								.catch(() => {
									quick_entry.dialog.working = false;
									reject();
								});
						});
					};

					HIDDEN_QUICK_ENTRY_FIELDS.forEach((fieldname) => {
						hide_field_completely(quick_entry, fieldname);
					});

					set_allowed_leave_types_query(quick_entry, []);

					quick_entry.set_query("employee", () => ({
						query: "erpnext.controllers.queries.employee_query",
					}));

					quick_entry.set_df_property(
						"employee",
						"read_only",
						!can_change_employee ? 1 : 0,
					);

					const refresh_for_current_state = () => {
						refresh_leave_metrics(quick_entry);
					};

					bind_input_change(quick_entry, "from_date", () => {
						refresh_allowed_leave_types(quick_entry).then(() => {
							refresh_for_current_state();
						});
					});
					bind_input_change(quick_entry, "to_date", refresh_for_current_state);
					bind_link_change(quick_entry, "leave_type", refresh_for_current_state);
					bind_link_change(quick_entry, "employee", () => {
						const employee = get_quick_entry_employee(quick_entry);
						Promise.all([
							sync_leave_approver(quick_entry, employee, { clear_existing: true }),
							refresh_allowed_leave_types(quick_entry),
						]).then(() => {
							refresh_for_current_state();
						});
					});

					Promise.all([
						sync_leave_approver(quick_entry, doc.employee),
						refresh_allowed_leave_types(quick_entry),
					]).then(() => {
						refresh_for_current_state();
					});
				},
				doc,
				true,
			);
		},
	},
	get_events_method: "hrms.hr.doctype.leave_application.leave_application.get_events",
};
