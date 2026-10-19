frappe.provide("hrms");

const OVERVIEW_METHOD = "hrms.overrides.employee_overview";
const COUNT = {
	slips: (n) => (n === 1 ? __("1 salary slip") : __("{0} salary slips", [n])),
	requests: (n) => (n === 1 ? __("1 request") : __("{0} requests", [n])),
	claims: (n) => (n === 1 ? __("1 claim") : __("{0} claims", [n])),
	advances: (n) => (n === 1 ? __("1 advance") : __("{0} advances", [n])),
	days: (n) => (flt(n) === 1 ? __("1 day") : __("{0} days", [flt(n)])),
};

frappe.ui.form.on("Employee", {
	refresh(frm) {
		if (frm.is_new() || !frm.get_field("overview_html")) return;
		if (!frm.employee_overview) frm.employee_overview = new hrms.EmployeeOverview(frm);
		frm.employee_overview.refresh();
	},
	on_tab_change(frm) {
		frm.employee_overview?.show();
	},
});

hrms.EmployeeOverview = class EmployeeOverview {
	static PERIODS = ["Current Fiscal Year", "Last 12 Months", "This Quarter", "Last Fiscal Year"];
	static RECENT_LIMIT = 10;
	static STATUS_THEME = {
		Submitted: "blue",
		Approved: "green",
		Paid: "green",
		Claimed: "green",
		Open: "orange",
		Unpaid: "orange",
		"Partially Paid": "orange",
		Withheld: "orange",
		Rejected: "red",
		Draft: "gray",
		Returned: "gray",
		"Partly Claimed and Returned": "gray",
		Cancelled: "gray",
	};
	static TRANSACTION_TYPES = [
		"Salary Slip",
		"Leave Application",
		"Expense Claim",
		"Employee Advance",
	];

	constructor(frm) {
		this.frm = frm;
		this.seq = 0;
	}

	pref(key) {
		try {
			return localStorage.getItem("employee-overview:" + key);
		} catch (e) {
			return null;
		}
	}
	set_pref(key, value) {
		try {
			localStorage.setItem("employee-overview:" + key, value);
		} catch (e) {
			return;
		}
	}

	refresh() {
		this.needs_refresh = true;
		this.show();
	}

	async show() {
		if (this.frm.get_active_tab()?.df.fieldname !== "overview_tab") return;
		if (!this.needs_refresh) return;
		await frappe.require(["desk_charts.bundle.js", "desk_charts.bundle.css"]);
		if (this.frm.get_active_tab()?.df.fieldname !== "overview_tab" || !this.needs_refresh)
			return;
		this.needs_refresh = false;
		if (this.employee !== this.frm.doc.name) this.build();
		this.check_activity();
	}

	build() {
		const { PERIODS } = hrms.EmployeeOverview;
		this.seq++;
		this.overview = null;
		this.list = null;
		this.employee = this.frm.doc.name;
		this.state = {
			period: PERIODS.includes(this.pref("period")) ? this.pref("period") : PERIODS[0],
			doc_type: "All",
		};
		this.destroy_trend();

		this.wrapper = this.frm.get_field("overview_html").$wrapper;
		this.wrapper.empty();
		this.$root = $('<div class="employee-overview">').appendTo(this.wrapper);
		this.build_header();
		this.build_sections();
	}

	build_header() {
		this.$header = $('<div class="eo-header">').appendTo(this.$root);
		const $controls = $('<div class="eo-header-controls">').appendTo(this.$header);
		this.$period = $('<div class="eo-period">').appendTo(this.$header);

		this.period_field = frappe.ui.form.make_control({
			parent: $('<div class="eo-filter">').appendTo($controls),
			df: {
				fieldtype: "Select",
				fieldname: "period",
				label: __("Period"),
				options: hrms.EmployeeOverview.PERIODS.join("\n"),
			},
			render_input: true,
			only_input: true,
		});
		this.period_field.refresh();
		this.period_field.set_value(this.state.period);
		this.period_field.$input.on("change", (e) => {
			if (e.target.value === this.state.period) return;
			this.state.period = e.target.value;
			this.set_pref("period", e.target.value);
			this.load();
		});
	}

	build_sections() {
		this.$body = $('<div class="eo-body">').appendTo(this.$root);
		this.$position = $('<div class="eo-section eo-kpis">').appendTo(this.$body);
		this.$trend = $('<div class="eo-section">').appendTo(this.$body);
		this.$charts = $('<div class="eo-section eo-two-col">').appendTo(this.$body);
		this.$pipeline = $('<div class="eo-section">').appendTo(this.$body);
		this.$recent = $('<div class="eo-section">').appendTo(this.$body);
		this.$empty = $('<div class="eo-section">').hide().appendTo(this.$root);

		this.build_recent();
		const employee = this.employee;
		frappe
			.require("embedded_list.bundle.js")
			.then(() => employee === this.employee && this.build_list())
			.catch((e) =>
				console.error("Employee Overview: failed to load embedded_list.bundle.js", e),
			);
	}

	check_activity() {
		const employee = this.employee;
		const token = (this.activity_seq = (this.activity_seq || 0) + 1);
		this.ready = false;
		return frappe
			.xcall(OVERVIEW_METHOD + ".has_activity", { employee })
			.then((active) => {
				if (employee !== this.employee || token !== this.activity_seq) return;
				if (!active) {
					this.render_no_activity();
					return;
				}
				this.$empty.hide();
				this.$header.show();
				this.$body.show();
				this.ready = true;
				this.load();
				this.refresh_list();
			})
			.catch(() => {
				if (employee !== this.employee || token !== this.activity_seq) return;
				this.needs_refresh = true;
				this.render_activity_error();
			});
	}

	refresh_list() {
		if (this.list && this.ready) this.list.refresh();
	}

	load() {
		if (!this.ready) return;
		const token = ++this.seq;
		this.overview = { loading: true };
		this.render();
		frappe
			.xcall(OVERVIEW_METHOD + ".get_employee_overview", {
				employee: this.employee,
				period: this.state.period,
			})
			.then((data) => ({ data }))
			.catch(() => ({ error: true }))
			.then((result) => {
				if (token !== this.seq) return;
				this.overview = result;
				if (result.data) this.currency = result.data.currency;
				this.render();
			});
	}

	render() {
		this.$period.text(this.period_text());
		this.render_position();
		this.render_trend();
		this.render_charts();
		this.render_pipeline();
	}

	render_no_activity() {
		const actions = ["Leave Application", "Expense Claim"]
			.filter((doctype) => frappe.model.can_create(doctype))
			.map((doctype) => ({
				label: __("New {0}", [__(doctype)]),
				icon: "plus",
				onclick: () => frappe.new_doc(doctype, { employee: this.frm.doc.name }),
			}));
		this.show_empty({
			icon: "inbox",
			title: __("No activity yet"),
			description: __(
				"Salary slips, attendance, leaves and expense claims for this employee will show up here.",
			),
			actions,
		});
	}

	render_activity_error() {
		this.show_empty({
			icon: "circle-alert",
			title: __("Could not load the overview"),
			description: __("Something went wrong while loading this employee's activity."),
			actions: [
				{ label: __("Try again"), icon: "refresh-cw", onclick: () => this.refresh() },
			],
		});
	}

	show_empty(opts) {
		this.$body.hide();
		this.$header.hide();
		this.$empty.empty().append(frappe.ui.empty_state(opts)).show();
	}

	get data() {
		return this.overview?.data;
	}

	section_error(section) {
		return this.overview?.error || this.data?.errors?.[section];
	}

	money(value) {
		return format_currency(flt(value), this.currency);
	}
	money0(value) {
		return format_currency(flt(value), this.currency, 0);
	}
	short_money(v) {
		const format = window.get_number_format(this.currency) || "";
		const country = format.includes(",##,") ? "India" : null;
		const n = flt(v);
		const short = frappe.utils.shorten_number(Math.abs(n), country, 4, 1);
		return (n < 0 ? "-" : "") + window.get_currency_symbol(this.currency) + (short || "0");
	}

	period_text() {
		const range = this.data?.period_range;
		if (!range) return "";
		const from = moment(range.from_date);
		const to = moment(range.to_date);
		const from_fmt = from.year() === to.year() ? "D MMM" : "D MMM YYYY";
		return from.format(from_fmt) + " – " + to.format("D MMM YYYY");
	}

	delta_opts(card) {
		if (card.delta === null || card.delta === undefined) return null;
		return { value: card.delta, positive_is_good: true, suffix: __("since last year") };
	}

	render_position() {
		const labels = [__("Gross Pay"), __("Net Pay"), __("Attendance"), __("Leave Balance")];
		let items;
		if (!this.overview || this.overview.loading) {
			items = labels.map((label) => ({ label, loading: true }));
		} else if (this.overview.error) {
			items = labels.map((label) => ({
				label,
				value: "—",
				caption: __("Could not load overview"),
			}));
		} else {
			items = [...this.pay_cards(), this.attendance_card(), this.leave_card()];
		}
		items = items.filter(Boolean);
		this.$position.toggle(!!items.length).empty().append(frappe.ui.stat_cards({ items }));
	}

	pay_cards() {
		const pay = this.data.pay;
		const labels = [__("Gross Pay"), __("Net Pay")];
		if (this.section_error("pay"))
			return labels.map((label) => ({
				label,
				value: "—",
				caption: __("Could not load salary slips"),
			}));
		if (!pay) return [];
		const open = () => this.list_route("Salary Slip", this.slip_filters());
		return [
			{
				label: labels[0],
				value: this.money0(pay.gross.value),
				delta: this.delta_opts(pay.gross),
				caption: pay.gross.count
					? COUNT.slips(pay.gross.count)
					: __("No salary slips in this period"),
				onclick: open,
			},
			{
				label: labels[1],
				value: this.money0(pay.net.value),
				caption: flt(pay.gross.value)
					? __("{0} deducted", [
							this.short_money(flt(pay.gross.value) - flt(pay.net.value)),
					  ])
					: __("No salary slips in this period"),
				onclick: open,
			},
		];
	}

	attendance_card() {
		const label = __("Attendance");
		if (this.section_error("attendance"))
			return { label, value: "—", caption: __("Could not load attendance") };
		const a = this.data.attendance;
		if (!a) return null;
		const open = () => this.list_route("Attendance", this.attendance_filters());
		if (a.rate == null) return { label, value: null, onclick: open };
		const counts = a.counts;
		return {
			label,
			value: flt(a.rate, 1) + "%",
			caption:
				[
					counts.Absent && __("{0} absent", [counts.Absent]),
					counts["On Leave"] && __("{0} on leave", [counts["On Leave"]]),
				]
					.filter(Boolean)
					.join(" · ") || __("{0} worked", [COUNT.days(a.days_worked)]),
			onclick: open,
		};
	}

	leave_card() {
		const label = __("Leave Balance");
		if (this.section_error("leave"))
			return { label, value: "—", caption: __("Could not load leave balances") };
		const l = this.data.leave;
		if (!l) return null;
		if (!l.types.length) return { label, value: null };
		return {
			label,
			value: COUNT.days(l.remaining),
			caption: flt(l.pending)
				? __("{0} pending approval", [COUNT.days(l.pending)])
				: __("Across {0} leave types", [l.types.length]),
			onclick: () => this.open_leave_balance(),
		};
	}

	destroy_trend() {
		if (this.trend_chart) this.trend_chart.destroy?.();
		this.trend_chart = null;
	}

	render_trend() {
		this.destroy_trend();
		this.$trend.empty();
		const pay = this.data?.pay;
		if (this.overview?.data && !pay && !this.section_error("pay")) {
			this.$trend.hide();
			return;
		}
		this.$trend.show();
		const $panel = this.panel(this.$trend, {
			title: __("Monthly Pay"),
			subtitle: __("Gross and net pay from submitted salary slips"),
			right: this.report_link(__("Salary Register"), () => this.open_salary_register()),
		});
		if (this.show_state($panel, 280, __("Could not load salary slips"), "pay")) return;
		if (!pay.points.some((p) => flt(p.gross) || flt(p.net))) {
			this.empty_note($panel, __("No salary slips in this period"), 220);
			return;
		}

		const $chart = $('<div class="eo-chart">').appendTo($panel);
		const style = getComputedStyle($chart[0]);
		const titles = pay.points.map((p) => p.title);
		this.trend_chart = new frappe.Chart($chart[0], {
			type: "bar",
			height: 260,
			colors: ["--eo-series-1", "--eo-series-2"].map((t) =>
				style.getPropertyValue(t).trim(),
			),
			data: {
				labels: pay.points.map((p) => p.label),
				datasets: [
					{ name: __("Gross Pay"), values: pay.points.map((p) => flt(p.gross)) },
					{ name: __("Net Pay"), values: pay.points.map((p) => flt(p.net)) },
				],
			},
			axisOptions: { xIsSeries: 1, shortenYAxisNumbers: 1 },
			tooltipOptions: {
				formatTooltipX: (label, index) => titles[index] || label,
				formatTooltipY: (v) => this.money0(v),
			},
			disableEntryAnimation: 1,
		});

		const paid = pay.points.filter((p) => flt(p.net));
		if (paid.length) {
			const avg = paid.reduce((sum, p) => sum + flt(p.net), 0) / paid.length;
			$('<div class="eo-note">')
				.text(__("Avg net pay {0} a month", [this.money0(avg)]))
				.appendTo($panel);
		}
	}

	render_charts() {
		(this.charts || []).forEach((chart) => chart.destroy?.());
		this.charts = [];
		this.$charts.empty();
		const data = this.data;
		const show_attendance =
			!data || data.attendance !== null || this.section_error("attendance");
		const show_leave = !data || data.leave !== null || this.section_error("leave");
		if (show_attendance) this.render_attendance();
		if (show_leave) this.render_leave();
		this.$charts.toggle(this.$charts.children().length > 0);
	}

	render_attendance() {
		const $panel = this.panel(this.$charts, {
			title: __("Attendance"),
			subtitle: __("Marked attendance in this period"),
			right: this.report_link(__("Attendance"), () =>
				this.list_route("Attendance", this.attendance_filters()),
			),
		});
		if (this.show_state($panel, 280, __("Could not load attendance"), "attendance")) return;
		const a = this.data.attendance;
		if (!a.marked) {
			this.empty_note($panel, __("No attendance marked in this period"), 180);
			return;
		}
		const c = a.counts;
		const segments = [
			{ label: __("Present"), value: c.Present, color: "--green-600" },
			{ label: __("Work From Home"), value: c["Work From Home"], color: "--green-400" },
			{ label: __("Half Day"), value: c["Half Day"], color: "--orange-400" },
			{ label: __("On Leave"), value: c["On Leave"], color: "--blue-400" },
			{ label: __("Absent"), value: c.Absent, color: "--red-500" },
		].filter((s) => s.value > 0);
		const $chart = $('<div class="eo-chart">').appendTo($panel);
		this.charts.push(
			new frappe.Chart($chart[0], {
				type: "donut",
				height: 300,
				data: {
					labels: segments.map((s) => s.label),
					datasets: [{ values: segments.map((s) => s.value) }],
				},
				colors: this.resolve_colors(
					$chart[0],
					segments.map((s) => s.color),
				),
				center: {
					value: String(a.marked),
					label: a.marked === 1 ? __("day") : __("days"),
				},
				tooltipOptions: { formatTooltipY: (v) => COUNT.days(v) },
			}),
		);
	}

	resolve_colors(el, tokens) {
		const style = getComputedStyle(el);
		return tokens.map((token) => style.getPropertyValue(token).trim());
	}

	render_leave() {
		const $panel = this.panel(this.$charts, {
			title: __("Leave Balance"),
			subtitle: __("Days left in the current allocation"),
			right: this.report_link(__("Employee Leave Balance"), () => this.open_leave_balance()),
		});
		if (this.show_state($panel, 180, __("Could not load leave balances"), "leave")) return;
		const l = this.data.leave;
		if (!l.types.length) {
			this.empty_note($panel, __("No leave allocated"), 180);
			return;
		}
		const $chart = $('<div class="eo-chart eo-bar-chart">').appendTo($panel);
		this.charts.push(
			new frappe.Chart($chart[0], {
				type: "bar",
				data: {
					labels: l.types.map((t) => t.leave_type),
					datasets: [
						{ name: __("Remaining"), values: l.types.map((t) => flt(t.remaining)) },
						{ name: __("Taken"), values: l.types.map((t) => flt(t.taken)) },
					],
				},
				colors: this.resolve_colors($chart[0], ["--eo-series-1", "--eo-series-2"]),
				barOptions: { horizontal: 1, stacked: 1, labelWidth: 120 },
				axisOptions: { numberFormatter: (v) => String(flt(v)) },
				tooltipOptions: { formatTooltipY: (v) => COUNT.days(v) },
			}),
		);
		const taken = l.types.reduce((sum, t) => sum + flt(t.taken), 0);
		$('<div class="eo-note">')
			.text(
				[
					__("{0} taken", [COUNT.days(taken)]),
					flt(l.pending) && __("{0} pending approval", [COUNT.days(l.pending)]),
				]
					.filter(Boolean)
					.join(" · "),
			)
			.appendTo($panel);
	}

	render_pipeline() {
		this.$pipeline.empty();
		const loading = !this.overview || this.overview.loading;
		const pl = this.data?.pipeline || {};
		const specs = this.pipeline_specs(pl).filter((s) => loading || s.data);
		if (!loading && !specs.length && !this.section_error("pipeline")) {
			this.$pipeline.hide();
			return;
		}
		this.$pipeline.show();
		this.section_head(this.$pipeline, { title: __("Pending Items") });
		if (loading) {
			const items = specs.map((s) => ({ label: s.label, loading: true }));
			frappe.ui.stat_cards({ items }).appendTo(this.$pipeline);
			return;
		}
		if (this.section_error("pipeline")) {
			this.empty_note(this.$pipeline, __("Could not load pending items"), 0).addClass(
				"eo-error",
			);
			return;
		}
		const items = specs.map((s) => ({
			label: s.label,
			value: s.value(s.data),
			caption: s.data.count ? s.caption(s.data) : s.empty,
			onclick: () => this.list_route(s.route[0], s.route[1]),
		}));
		frappe.ui.stat_cards({ items }).appendTo(this.$pipeline);
	}

	pipeline_specs(pl) {
		const employee = this.frm.doc.name;
		const specs = [];
		if (frappe.model.can_read("Leave Application"))
			specs.push({
				label: __("Leave Requests"),
				data: pl.leave_requests,
				value: (d) => COUNT.days(d.value),
				caption: (d) =>
					[COUNT.requests(d.count), d.started && __("{0} already started", [d.started])]
						.filter(Boolean)
						.join(" · "),
				empty: __("Nothing awaiting approval"),
				route: ["Leave Application", { employee, status: "Open", docstatus: 0 }],
			});
		if (frappe.model.can_read("Expense Claim"))
			specs.push(
				{
					label: __("Claims Awaiting Approval"),
					data: pl.claims_awaiting,
					value: (d) => this.money0(d.value),
					caption: (d) => COUNT.claims(d.count),
					empty: __("Nothing awaiting approval"),
					route: ["Expense Claim", { employee, approval_status: "Draft", docstatus: 0 }],
				},
				{
					label: __("Claims to Reimburse"),
					data: pl.claims_unpaid,
					value: (d) => this.money0(d.value),
					caption: (d) => COUNT.claims(d.count) + " · " + __("approved, not paid"),
					empty: __("Nothing to reimburse"),
					route: [
						"Expense Claim",
						{ employee, docstatus: 1, status: ["in", ["Unpaid", "Partially Paid"]] },
					],
				},
			);
		if (frappe.model.can_read("Employee Advance"))
			specs.push({
				label: __("Advances to Settle"),
				data: pl.advances,
				value: (d) => this.money0(d.value),
				caption: (d) =>
					[
						COUNT.advances(d.count),
						flt(d.to_pay) && __("{0} yet to be paid", [this.short_money(d.to_pay)]),
					]
						.filter(Boolean)
						.join(" · "),
				empty: __("Nothing outstanding"),
				route: ["Employee Advance", { employee, docstatus: 1 }],
			});
		return specs;
	}

	show_state($panel, height, error_text, section) {
		if (!this.overview || this.overview.loading) {
			$panel.attr("aria-busy", "true");
			$('<div class="eo-placeholder">')
				.css("height", height)
				.append(frappe.ui.skeleton({ width: "100%", height: "100%" }))
				.appendTo($panel);
			return true;
		}
		if (this.section_error(section)) {
			this.empty_note($panel, error_text, height).addClass("eo-error");
			return true;
		}
		return false;
	}

	empty_note($panel, text, height) {
		return $('<div class="eo-empty">').css("min-height", height).text(text).appendTo($panel);
	}

	build_recent() {
		this.section_head(this.$recent, {
			title: __("Recent Transactions"),
			right: this.build_type_filter(),
		});
		this.$list = $('<div class="eo-list">').appendTo(this.$recent);
	}

	build_type_filter() {
		const types = ["All", ...hrms.EmployeeOverview.TRANSACTION_TYPES];
		const $holder = $('<div class="eo-filter">');
		const control = frappe.ui.form.make_control({
			parent: $holder,
			df: {
				fieldtype: "Select",
				fieldname: "doc_type",
				options: types
					.map((t) => (t === "All" ? __("All Document Types") : __(t)))
					.join("\n"),
			},
			render_input: true,
			only_input: true,
		});
		control.refresh();
		control.set_value(__("All Document Types"));
		control.$input.on("change", () => {
			this.state.doc_type = types[control.$input.prop("selectedIndex")] || "All";
			this.refresh_list();
		});
		return $holder;
	}

	build_list() {
		const me = this;
		const { RECENT_LIMIT, STATUS_THEME } = hrms.EmployeeOverview;
		this.list = new frappe.ui.EmbeddedList({
			wrapper: this.$list,
			show_search: false,
			page_size: RECENT_LIMIT,
			empty_message: __("No transactions yet"),
			empty_icon: "list",
			columns: [
				{
					label: __("Document"),
					fieldname: "name",
					type: "link",
					route: (row) => ["Form", row.doctype, row.name],
				},
				{ label: __("Type"), fieldname: "type_label" },
				{ label: __("Date"), render: (row) => frappe.datetime.str_to_user(row.date) },
				{
					label: __("Status"),
					fieldname: "status",
					type: "badge",
					color: (row) => STATUS_THEME[row.status] || "gray",
				},
				{ label: __("Amount"), render: (row) => me.amount_cell(row) },
				{ label: __("Outstanding"), render: (row) => me.outstanding_cell(row) },
			],
			get_data() {
				if (!me.ready) return Promise.resolve([]);
				return frappe.xcall(OVERVIEW_METHOD + ".get_employee_transactions", {
					employee: me.frm.doc.name,
					doc_type: me.state.doc_type,
					limit: RECENT_LIMIT,
				});
			},
		});
		this.refresh_list();
	}

	amount_cell(row) {
		if (row.days != null) return `<div class="text-right">${COUNT.days(row.days)}</div>`;
		return `<div class="text-right">${format_currency(flt(row.amount), row.currency)}</div>`;
	}

	outstanding_cell(row) {
		if (row.outstanding == null || flt(row.outstanding) <= 0)
			return '<div class="text-right text-ink-gray-4">—</div>';
		return `<div class="text-right">${format_currency(
			flt(row.outstanding),
			row.currency,
		)}</div>`;
	}

	section_head($parent, { title, subtitle, right } = {}) {
		const $head = $('<div class="eo-head">').appendTo($parent);
		const $top = $('<div class="eo-head-top">').appendTo($head);
		$('<div class="eo-title">').text(title).appendTo($top);
		if (right) $('<div class="eo-head-action">').append(right).appendTo($top);
		if (subtitle) $('<div class="eo-subtitle">').text(subtitle).appendTo($head);
		return $head;
	}

	panel($parent, opts = {}) {
		const $panel = $('<div class="eo-panel">').appendTo($parent);
		if (opts.title) this.section_head($panel, opts);
		return $panel;
	}

	report_link(text, on_click) {
		return frappe.ui.button({
			label: text,
			variant: "ghost",
			size: "sm",
			icon_right: "arrow-up-right",
			onclick: on_click,
		});
	}

	period_range() {
		return this.data?.period_range || {};
	}

	slip_filters() {
		const range = this.period_range();
		return {
			employee: this.frm.doc.name,
			docstatus: 1,
			start_date: ["between", [range.from_date, range.to_date]],
		};
	}

	attendance_filters() {
		const range = this.period_range();
		return {
			employee: this.frm.doc.name,
			docstatus: 1,
			attendance_date: ["between", [range.from_date, range.to_date]],
		};
	}

	open_salary_register() {
		const range = this.period_range();
		frappe.route_options = {
			company: this.frm.doc.company,
			employee: this.frm.doc.name,
			from_date: range.from_date,
			to_date: range.to_date,
			docstatus: "Submitted",
		};
		frappe.set_route("query-report", "Salary Register");
	}

	open_leave_balance() {
		frappe.route_options = {
			company: this.frm.doc.company,
			employee: this.frm.doc.name,
		};
		frappe.set_route("query-report", "Employee Leave Balance");
	}

	list_route(doctype, filters) {
		frappe.route_options = filters;
		frappe.set_route("List", doctype);
	}
};
