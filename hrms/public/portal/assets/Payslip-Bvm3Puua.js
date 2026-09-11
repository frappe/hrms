import {
	L as E,
	v as F,
	o as f,
	d as G,
	w as t,
	h as P,
	f as a,
	g as r,
	I as N,
	e as m,
	k as p,
	t as i,
	z as D,
	F as M,
	u as T,
	a as y,
} from "./frappe-ui-rHlwnvVy.js";
import { a as U, _ as d, b as A } from "./SectionCard-0tgyDAFI.js";
import { _ as H } from "./DashGrid-Cmnm2mAO.js";
import { _ as S } from "./DataTable-BY05XQx8.js";
import { _ as L } from "./StatTiles-DcUJsMoQ.js";
import { _ as Y } from "./StatusBadge-ZWn2FvVw.js";
import { _ as s } from "./FieldRow-C13lI4HG.js";
import { _ as b } from "./TotalRow-DkNHj82l.js";
import { b as z, d as C, i as v, a as I } from "./index-6wvshjQq.js";
import "./EmptyState-0_BFjfJU.js";
const O = { key: 0, class: "px-3.5 pb-3.5 text-sm text-ink-gray-5" },
	W = { class: "flex flex-col" },
	j = { class: "flex flex-col" },
	q = { class: "flex flex-col" },
	J = { class: "flex flex-col" },
	ue = {
		__name: "Payslip",
		setup(K) {
			const g = T(),
				e = y(() => v.data),
				_ = y(() => {
					var l;
					return ((l = e.value) == null ? void 0 : l.attendance) || {};
				}),
				k = [
					{ key: "salary_component", label: "Component", primary: !0 },
					{ key: "amount", label: "Amount", align: "right", nums: !0 },
					{
						key: "year_to_date",
						label: "Year to Date",
						align: "right",
						nums: !0,
						muted: !0,
						hideOnMobile: !0,
					},
				],
				R = y(() => {
					var l, u, o, x, $;
					return [
						{
							label: "Gross Pay",
							value: n((l = e.value) == null ? void 0 : l.gross_pay),
						},
						{
							label: "Deductions",
							value: n((u = e.value) == null ? void 0 : u.total_deduction),
						},
						{
							label: "Net Pay",
							value: n(
								((o = e.value) == null ? void 0 : o.rounded_total) ||
									((x = e.value) == null ? void 0 : x.net_pay),
							),
							hint: ($ = e.value) == null ? void 0 : $.period,
						},
					];
				});
			function n(l) {
				var u;
				return I(l, { currency: (u = e.value) == null ? void 0 : u.currency });
			}
			function c(l) {
				return l == null ? "—" : Number(l) === 1 ? "1 day" : `${Number(l)} days`;
			}
			function h(l) {
				const u = new URLSearchParams({ name: e.value.name });
				return l && u.set("inline", "1"), `/api/method/hrms.api.portal.payslip_pdf?${u}`;
			}
			function B() {
				window.open(h(!0), "_blank", "noopener");
			}
			function V() {
				const l = document.createElement("a");
				(l.href = h(!1)), (l.rel = "noopener"), l.click();
			}
			function w() {
				v.fetch({ name: g.params.name });
			}
			return (
				E(w),
				F(() => g.params.name, w),
				(l, u) => (
					f(),
					G(
						A,
						{ loading: r(v).loading && !r(v).data },
						{
							default: t(() => [
								e.value
									? (f(),
									  P(
											M,
											{ key: 0 },
											[
												a(
													U,
													{
														subtitle: `${r(z)(
															e.value.start_date,
															e.value.end_date,
														)} · paid ${r(C)(e.value.posting_date)}`,
														crumbs: [
															{ label: "Payslips", to: "/payslips" },
															{ label: e.value.period },
														],
													},
													{
														actions: t(() => [
															a(r(N), {
																variant: "subtle",
																icon: "lucide-download",
																label: "Download PDF",
																onClick: V,
															}),
															a(r(N), {
																variant: "subtle",
																icon: "lucide-printer",
																label: "Print",
																onClick: B,
															}),
														]),
														_: 1,
													},
													8,
													["subtitle", "crumbs"],
												),
												a(L, { tiles: R.value }, null, 8, ["tiles"]),
												a(H, null, {
													main: t(() => [
														a(
															d,
															{ title: "Earnings", padded: !1 },
															{
																default: t(() => [
																	a(
																		S,
																		{
																			columns: k,
																			rows: e.value.earnings,
																			"id-key":
																				"salary_component",
																			"empty-message":
																				"No earnings on this payslip.",
																		},
																		{
																			"cell-amount": t(
																				({ row: o }) => [
																					p(
																						i(
																							n(
																								o.amount,
																							),
																						),
																						1,
																					),
																				],
																			),
																			"cell-year_to_date": t(
																				({ row: o }) => [
																					p(
																						i(
																							n(
																								o.year_to_date,
																							),
																						),
																						1,
																					),
																				],
																			),
																			_: 1,
																		},
																		8,
																		["rows"],
																	),
																	a(
																		b,
																		{
																			label: "Gross Pay",
																			value: n(
																				e.value.gross_pay,
																			),
																		},
																		null,
																		8,
																		["value"],
																	),
																]),
																_: 1,
															},
														),
														a(
															d,
															{ title: "Deductions", padded: !1 },
															{
																default: t(() => [
																	a(
																		S,
																		{
																			columns: k,
																			rows: e.value
																				.deductions,
																			"id-key":
																				"salary_component",
																			"empty-message":
																				"Nothing was deducted.",
																		},
																		{
																			"cell-amount": t(
																				({ row: o }) => [
																					p(
																						i(
																							n(
																								o.amount,
																							),
																						),
																						1,
																					),
																				],
																			),
																			"cell-year_to_date": t(
																				({ row: o }) => [
																					p(
																						i(
																							n(
																								o.year_to_date,
																							),
																						),
																						1,
																					),
																				],
																			),
																			_: 1,
																		},
																		8,
																		["rows"],
																	),
																	a(
																		b,
																		{
																			label: "Total Deductions",
																			value: n(
																				e.value
																					.total_deduction,
																			),
																		},
																		null,
																		8,
																		["value"],
																	),
																]),
																_: 1,
															},
														),
														a(
															d,
															{ title: "Net Pay", padded: !1 },
															{
																default: t(() => [
																	a(
																		b,
																		{
																			label: "Take home",
																			value: n(
																				e.value
																					.rounded_total ||
																					e.value
																						.net_pay,
																			),
																			strong: "",
																		},
																		null,
																		8,
																		["value"],
																	),
																	e.value.total_in_words
																		? (f(),
																		  P(
																				"p",
																				O,
																				i(
																					e.value
																						.total_in_words,
																				),
																				1,
																		  ))
																		: D("", !0),
																]),
																_: 1,
															},
														),
													]),
													side: t(() => [
														a(
															d,
															{ title: "Status" },
															{
																action: t(() => [
																	a(
																		Y,
																		{ status: e.value.status },
																		null,
																		8,
																		["status"],
																	),
																]),
																default: t(() => [
																	m("dl", W, [
																		a(
																			s,
																			{
																				label: "Period",
																				value: e.value
																					.period,
																			},
																			null,
																			8,
																			["value"],
																		),
																		a(
																			s,
																			{
																				label: "Paid on",
																				value: r(C)(
																					e.value
																						.posting_date,
																				),
																				nums: "",
																			},
																			null,
																			8,
																			["value"],
																		),
																		a(
																			s,
																			{
																				label: "Mode",
																				value: e.value
																					.mode_of_payment,
																			},
																			null,
																			8,
																			["value"],
																		),
																	]),
																]),
																_: 1,
															},
														),
														a(
															d,
															{
																title: "Days",
																"readonly-label": "HR-owned",
															},
															{
																default: t(() => [
																	m("dl", j, [
																		a(
																			s,
																			{
																				label: "Working days",
																				value: c(
																					_.value
																						.total_working_days,
																				),
																				locked: "",
																				nums: "",
																			},
																			null,
																			8,
																			["value"],
																		),
																		a(
																			s,
																			{
																				label: "Payable days",
																				value: c(
																					_.value
																						.payment_days,
																				),
																				locked: "",
																				nums: "",
																			},
																			null,
																			8,
																			["value"],
																		),
																		a(
																			s,
																			{
																				label: "Unpaid leave",
																				value: c(
																					_.value
																						.leave_without_pay,
																				),
																				locked: "",
																				nums: "",
																			},
																			null,
																			8,
																			["value"],
																		),
																		a(
																			s,
																			{
																				label: "Absent",
																				value: c(
																					_.value
																						.absent_days,
																				),
																				locked: "",
																				nums: "",
																			},
																			null,
																			8,
																			["value"],
																		),
																	]),
																]),
																_: 1,
															},
														),
														a(
															d,
															{ title: "Year to Date" },
															{
																default: t(() => [
																	m("dl", q, [
																		a(
																			s,
																			{
																				label: "Gross",
																				value: n(
																					e.value
																						.gross_year_to_date,
																				),
																				nums: "",
																			},
																			null,
																			8,
																			["value"],
																		),
																		a(
																			s,
																			{
																				label: "Net",
																				value: n(
																					e.value
																						.year_to_date,
																				),
																				nums: "",
																			},
																			null,
																			8,
																			["value"],
																		),
																	]),
																]),
																_: 1,
															},
														),
														a(
															d,
															{
																title: "Salary Structure",
																"readonly-label": "HR-owned",
															},
															{
																default: t(() => [
																	m("dl", J, [
																		a(
																			s,
																			{
																				label: "Structure",
																				value: e.value
																					.salary_structure,
																				locked: "",
																			},
																			null,
																			8,
																			["value"],
																		),
																	]),
																]),
																_: 1,
															},
														),
													]),
													_: 1,
												}),
											],
											64,
									  ))
									: D("", !0),
							]),
							_: 1,
						},
						8,
						["loading"],
					)
				)
			);
		},
	};
export { ue as default };
