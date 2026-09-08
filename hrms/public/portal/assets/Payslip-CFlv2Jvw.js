import {
	o as f,
	s as h,
	k as c,
	x as d,
	v as V,
	u as A,
	P as E,
	w as F,
	f as G,
	g as t,
	F as U,
	h as a,
	i as r,
	M as D,
	B as v,
	C as S,
	a as g,
} from "./frappe-ui-BQ9PgXrr.js";
import { _ as i, a as H } from "./SectionCard-u_7VCKnT.js";
import { _ as Y } from "./PageHead-3jtDpZ9g.js";
import { _ as j } from "./DashGrid-Bd23iLvt.js";
import { _ as C } from "./DataTable-vZ6Z-J3d.js";
import { _ as z } from "./StatTiles-YoNxs_Qn.js";
import { _ as L } from "./StatusBadge-Bqz4zlkD.js";
import { _ as s } from "./FieldRow-DbBPtAxY.js";
import { c as O, d as B, i as y, b as W } from "./index-DKSqIuAQ.js";
import "./EmptyState-DNwecFw5.js";
const q = {
		class: "flex items-baseline justify-between gap-3 border-t border-outline-gray-2 px-3.5 py-2.5",
	},
	I = { class: "text-base text-ink-gray-5" },
	k = {
		__name: "TotalRow",
		props: { label: String, value: [String, Number], strong: Boolean },
		setup(_) {
			return (b, e) => (
				f(),
				h("div", q, [
					c("span", I, d(_.label), 1),
					c(
						"span",
						{
							class: V([
								"nums shrink-0 font-semibold text-ink-gray-9",
								_.strong ? "text-lg" : "text-base",
							]),
						},
						d(_.value),
						3,
					),
				])
			);
		},
	},
	J = { key: 0, class: "px-3.5 pb-3.5 text-sm text-ink-gray-5" },
	K = { class: "flex flex-col" },
	Q = { class: "flex flex-col" },
	X = { class: "flex flex-col" },
	Z = { class: "flex flex-col" },
	de = {
		__name: "Payslip",
		setup(_) {
			const b = A(),
				e = g(() => y.data),
				m = g(() => {
					var l;
					return ((l = e.value) == null ? void 0 : l.attendance) || {};
				}),
				x = [
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
				R = g(() => {
					var l, u, o, P, N;
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
									((P = e.value) == null ? void 0 : P.net_pay),
							),
							hint: (N = e.value) == null ? void 0 : N.period,
						},
					];
				});
			function n(l) {
				var u;
				return W(l, { currency: (u = e.value) == null ? void 0 : u.currency });
			}
			function p(l) {
				return l == null ? "—" : Number(l) === 1 ? "1 day" : `${Number(l)} days`;
			}
			function w(l) {
				const u = new URLSearchParams({ name: e.value.name });
				return l && u.set("inline", "1"), `/api/method/hrms.api.portal.payslip_pdf?${u}`;
			}
			function M() {
				window.open(w(!0), "_blank", "noopener");
			}
			function T() {
				const l = document.createElement("a");
				(l.href = w(!1)), (l.rel = "noopener"), l.click();
			}
			function $() {
				y.fetch({ name: b.params.name });
			}
			return (
				E($),
				F(() => b.params.name, $),
				(l, u) => (
					f(),
					G(
						H,
						{ loading: r(y).loading && !r(y).data },
						{
							default: t(() => [
								e.value
									? (f(),
									  h(
											U,
											{ key: 0 },
											[
												a(
													Y,
													{
														subtitle: `${r(O)(
															e.value.start_date,
															e.value.end_date,
														)} · paid ${r(B)(e.value.posting_date)}`,
														crumbs: [
															{ label: "Payslips", to: "/payslips" },
															{ label: e.value.period },
														],
													},
													{
														actions: t(() => [
															a(r(D), {
																variant: "subtle",
																icon: "download",
																label: "Download PDF",
																onClick: T,
															}),
															a(r(D), {
																variant: "subtle",
																icon: "printer",
																label: "Print",
																onClick: M,
															}),
														]),
														_: 1,
													},
													8,
													["subtitle", "crumbs"],
												),
												a(z, { tiles: R.value }, null, 8, ["tiles"]),
												a(j, null, {
													main: t(() => [
														a(
															i,
															{ title: "Earnings", padded: !1 },
															{
																default: t(() => [
																	a(
																		C,
																		{
																			columns: x,
																			rows: e.value.earnings,
																			"id-key":
																				"salary_component",
																			"empty-message":
																				"No earnings on this payslip.",
																		},
																		{
																			"cell-amount": t(
																				({ row: o }) => [
																					v(
																						d(
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
																					v(
																						d(
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
																		k,
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
															i,
															{ title: "Deductions", padded: !1 },
															{
																default: t(() => [
																	a(
																		C,
																		{
																			columns: x,
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
																					v(
																						d(
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
																					v(
																						d(
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
																		k,
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
															i,
															{ title: "Net Pay", padded: !1 },
															{
																default: t(() => [
																	a(
																		k,
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
																		  h(
																				"p",
																				J,
																				d(
																					e.value
																						.total_in_words,
																				),
																				1,
																		  ))
																		: S("", !0),
																]),
																_: 1,
															},
														),
													]),
													side: t(() => [
														a(
															i,
															{ title: "Status" },
															{
																action: t(() => [
																	a(
																		L,
																		{ status: e.value.status },
																		null,
																		8,
																		["status"],
																	),
																]),
																default: t(() => [
																	c("dl", K, [
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
																				value: r(B)(
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
																		a(
																			s,
																			{
																				label: "Account",
																				value: e.value
																					.bank_account,
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
															i,
															{
																title: "Days",
																"readonly-label": "HR-owned",
															},
															{
																default: t(() => [
																	c("dl", Q, [
																		a(
																			s,
																			{
																				label: "Working days",
																				value: p(
																					m.value
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
																				value: p(
																					m.value
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
																				value: p(
																					m.value
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
																				value: p(
																					m.value
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
															i,
															{ title: "Year to Date" },
															{
																default: t(() => [
																	c("dl", X, [
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
															i,
															{
																title: "Salary Structure",
																"readonly-label": "HR-owned",
															},
															{
																default: t(() => [
																	c("dl", Z, [
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
									: S("", !0),
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
export { de as default };
