var D = (O, $, m) =>
	new Promise((C, l) => {
		var d = (r) => {
				try {
					u(m.next(r));
				} catch (_) {
					l(_);
				}
			},
			c = (r) => {
				try {
					u(m.throw(r));
				} catch (_) {
					l(_);
				}
			},
			u = (r) => (r.done ? C(r.value) : Promise.resolve(r.value).then(d, c));
		u((m = m.apply(O, $)).next());
	});
import {
	v as G,
	L as H,
	o as b,
	d as J,
	w as o,
	f as t,
	g as s,
	I as S,
	e as g,
	S as X,
	h as V,
	F as E,
	t as v,
	z as B,
	k as P,
	O as Y,
	B as h,
	a as q,
	b as K,
} from "./frappe-ui-D0k6koYp.js";
import { a as Q, _ as R, b as W } from "./SectionCard-C5Qs8pBJ.js";
import { _ as Z } from "./DashGrid-CGnJY6QD.js";
import { _ as ee } from "./DataTable-BPI_hH2T.js";
import { _ as ae } from "./StatTiles-CcQndbp7.js";
import { _ as M } from "./StatusBadge-sSVuNJEI.js";
import { _ as w } from "./FieldRow-DoxIhPye.js";
import { _ as F } from "./DateField-DafgtgxX.js";
import { p as y, d as k, a as x } from "./index-BSaIzYPn.js";
import { n as le, a as I, e as L } from "./toast-BPVivXt-.js";
import "./EmptyState-38_uLDf3.js";
const te = { class: "flex flex-wrap items-center gap-2" },
	oe = { key: 1, class: "text-base text-ink-gray-5" },
	se = { class: "font-semibold text-ink-gray-9" },
	ne = { class: "flex flex-col" },
	ie = { class: "flex flex-col" },
	he = {
		__name: "Payslips",
		setup(O) {
			const $ = [
					{ key: "period", label: "Period", primary: !0 },
					{
						key: "gross_pay",
						label: "Gross",
						align: "right",
						nums: !0,
						muted: !0,
						hideOnMobile: !0,
					},
					{
						key: "total_deduction",
						label: "Deductions",
						align: "right",
						nums: !0,
						muted: !0,
						hideOnMobile: !0,
					},
					{ key: "net_pay", label: "Net Pay", align: "right", nums: !0 },
					{ key: "status", label: "Status", align: "right", badge: !0 },
					{ key: "download", label: "", align: "right", track: "2.25rem" },
				],
				m = [
					{ label: "Past 3 months", value: "3m" },
					{ label: "Past 6 months", value: "6m" },
					{ label: "Past year", value: "12m" },
					{ label: "All", value: "all" },
					{ label: "Custom", value: "custom" },
				],
				C = K(),
				l = q(() => y.data),
				d = h("12m"),
				c = h(""),
				u = h(""),
				r = h(!1);
			function _() {
				(d.value === "custom" && !(c.value && u.value)) ||
					y.fetch({
						period: d.value,
						from_date: c.value || void 0,
						to_date: u.value || void 0,
					});
			}
			G([d, c, u], _);
			function U(n, a) {
				const i = URL.createObjectURL(n),
					p = document.createElement("a");
				(p.href = i), (p.download = a), p.click(), URL.revokeObjectURL(i);
			}
			function j(n) {
				return D(this, null, function* () {
					try {
						const a = yield fetch(
							`/api/method/hrms.api.portal.payslip_pdf?name=${encodeURIComponent(
								n.name,
							)}`,
						);
						if (!a.ok) throw new Error(yield a.text());
						U(yield a.blob(), `${n.period.replace(" ", "-")}-payslip.pdf`);
					} catch (a) {
						I("Could not download", L(a, "Try again in a moment."));
					}
				});
			}
			function z(n) {
				C.push(`/payslips/${encodeURIComponent(n.name)}`);
			}
			function A() {
				return D(this, null, function* () {
					var a;
					const n = (((a = l.value) == null ? void 0 : a.slips) || []).map(
						(i) => i.name,
					);
					if (n.length) {
						r.value = !0;
						try {
							const i = yield fetch("/api/method/hrms.api.portal.payslips_zip", {
								method: "POST",
								headers: {
									"Content-Type": "application/json",
									Accept: "application/json",
									"X-Frappe-CSRF-Token": window.csrf_token,
								},
								body: JSON.stringify({ names: n }),
							});
							if (!i.ok) throw new Error(yield i.text());
							U(yield i.blob(), "payslips.zip"),
								le(`${n.length} payslips downloaded`);
						} catch (i) {
							I("Could not download", L(i, "Try again in a moment."));
						} finally {
							r.value = !1;
						}
					}
				});
			}
			return (
				H(() => y.fetch()),
				(n, a) => (
					b(),
					J(
						W,
						{ loading: s(y).loading && !s(y).data },
						{
							default: o(() => {
								var i, p;
								return [
									t(
										Q,
										{ title: "Payslips", subtitle: "Your salary history" },
										{
											actions: o(() => {
												var e, f, N, T;
												return [
													t(
														s(S),
														{
															variant: "subtle",
															"icon-left": "lucide-download",
															disabled: !(
																(f =
																	(e = l.value) == null
																		? void 0
																		: e.slips) != null &&
																f.length
															),
															loading: r.value,
															label:
																(T =
																	(N = l.value) == null
																		? void 0
																		: N.slips) != null &&
																T.length
																	? `Download ${l.value.slips.length}`
																	: "Download",
															onClick: A,
														},
														null,
														8,
														["disabled", "loading", "label"],
													),
												];
											}),
											_: 1,
										},
									),
									g("div", te, [
										t(
											s(X),
											{
												modelValue: d.value,
												"onUpdate:modelValue":
													a[0] || (a[0] = (e) => (d.value = e)),
												options: m,
												class: "w-44",
											},
											null,
											8,
											["modelValue"],
										),
										d.value === "custom"
											? (b(),
											  V(
													E,
													{ key: 0 },
													[
														t(
															F,
															{
																modelValue: c.value,
																"onUpdate:modelValue":
																	a[1] ||
																	(a[1] = (e) => (c.value = e)),
																placeholder: "From",
																class: "w-44",
															},
															null,
															8,
															["modelValue"],
														),
														t(
															F,
															{
																modelValue: u.value,
																"onUpdate:modelValue":
																	a[2] ||
																	(a[2] = (e) => (u.value = e)),
																placeholder: "To",
																class: "w-44",
															},
															null,
															8,
															["modelValue"],
														),
													],
													64,
											  ))
											: (p = (i = l.value) == null ? void 0 : i.range) !=
														null && p.from_date
											  ? (b(),
											    V(
														"span",
														oe,
														v(s(k)(l.value.range.from_date)) +
															" to " +
															v(s(k)(l.value.range.to_date)),
														1,
											    ))
											  : B("", !0),
									]),
									l.value
										? (b(),
										  V(
												E,
												{ key: 0 },
												[
													t(ae, { tiles: n.tiles }, null, 8, ["tiles"]),
													t(Z, null, {
														main: o(() => [
															t(
																R,
																{
																	title: "Monthly Payslips",
																	padded: !1,
																},
																{
																	default: o(() => [
																		t(
																			ee,
																			{
																				columns: $,
																				rows: l.value
																					.slips,
																				clickable: "",
																				"empty-message":
																					"No payslips in this period.",
																				onRowClick: z,
																			},
																			{
																				"cell-gross_pay":
																					o(
																						({
																							row: e,
																						}) => [
																							P(
																								v(
																									s(
																										x,
																									)(
																										e.gross_pay,
																									),
																								),
																								1,
																							),
																						],
																					),
																				"cell-total_deduction":
																					o(
																						({
																							row: e,
																						}) => [
																							P(
																								v(
																									s(
																										x,
																									)(
																										e.total_deduction,
																									),
																								),
																								1,
																							),
																						],
																					),
																				"cell-net_pay": o(
																					({
																						row: e,
																					}) => [
																						g(
																							"span",
																							se,
																							v(
																								s(
																									x,
																								)(
																									e.net_pay,
																								),
																							),
																							1,
																						),
																					],
																				),
																				"cell-status": o(
																					({
																						row: e,
																					}) => [
																						t(
																							M,
																							{
																								status:
																									e.docstatus ===
																									1
																										? e.status
																										: "Draft",
																							},
																							null,
																							8,
																							[
																								"status",
																							],
																						),
																					],
																				),
																				"cell-download": o(
																					({
																						row: e,
																					}) => [
																						t(
																							s(S),
																							{
																								variant:
																									"ghost",
																								icon: "lucide-download",
																								label: `Download ${e.period}`,
																								onClick:
																									Y(
																										(
																											f,
																										) =>
																											j(
																												e,
																											),
																										[
																											"stop",
																										],
																									),
																							},
																							null,
																							8,
																							[
																								"label",
																								"onClick",
																							],
																						),
																					],
																				),
																				_: 1,
																			},
																			8,
																			["rows"],
																		),
																	]),
																	_: 1,
																},
															),
														]),
														side: o(() => [
															t(
																R,
																{ title: "Tax Declaration" },
																{
																	action: o(() => [
																		t(
																			M,
																			{
																				status: l.value.tax
																					.has_declaration
																					? "submitted"
																					: "due",
																				label: l.value.tax
																					.has_declaration
																					? "Submitted"
																					: "Not declared",
																			},
																			null,
																			8,
																			["status", "label"],
																		),
																	]),
																	default: o(() => [
																		g("dl", ne, [
																			t(
																				w,
																				{
																					label: "Declared",
																					value: s(x)(
																						l.value.tax
																							.declared,
																					),
																					nums: "",
																				},
																				null,
																				8,
																				["value"],
																			),
																			t(
																				w,
																				{
																					label: "Period ends",
																					value: l.value
																						.tax
																						.period_end
																						? s(k)(
																								l
																									.value
																									.tax
																									.period_end,
																						  )
																						: "",
																					nums: "",
																				},
																				null,
																				8,
																				["value"],
																			),
																		]),
																		t(
																			s(S),
																			{
																				variant: "subtle",
																				class: "mt-1 w-full",
																				onClick:
																					a[3] ||
																					(a[3] = (e) =>
																						n.desk(
																							"employee-tax-exemption-declaration",
																						)),
																			},
																			{
																				default: o(() => [
																					...(a[4] ||
																						(a[4] = [
																							P(
																								" Declare Investments ",
																								-1,
																							),
																						])),
																				]),
																				_: 1,
																			},
																		),
																	]),
																	_: 1,
																},
															),
															t(
																R,
																{
																	title: "Salary Structure",
																	"readonly-label": "HR-owned",
																},
																{
																	default: o(() => {
																		var e, f;
																		return [
																			g("dl", ie, [
																				t(
																					w,
																					{
																						label: "Structure",
																						value:
																							(e =
																								l
																									.value
																									.structure) ==
																							null
																								? void 0
																								: e.salary_structure,
																						locked: "",
																					},
																					null,
																					8,
																					["value"],
																				),
																				t(
																					w,
																					{
																						label: "Effective",
																						value:
																							(f =
																								l
																									.value
																									.structure) !=
																								null &&
																							f.from_date
																								? s(
																										k,
																								  )(
																										l
																											.value
																											.structure
																											.from_date,
																								  )
																								: "",
																						locked: "",
																						nums: "",
																					},
																					null,
																					8,
																					["value"],
																				),
																			]),
																		];
																	}),
																	_: 1,
																},
															),
														]),
														_: 1,
													}),
												],
												64,
										  ))
										: B("", !0),
								];
							}),
							_: 1,
						},
						8,
						["loading"],
					)
				)
			);
		},
	};
export { he as default };
