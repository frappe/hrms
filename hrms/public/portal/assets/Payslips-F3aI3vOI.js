var k = (R, h, m) =>
	new Promise((w, t) => {
		var d = (n) => {
				try {
					u(m.next(n));
				} catch (_) {
					t(_);
				}
			},
			c = (n) => {
				try {
					u(m.throw(n));
				} catch (_) {
					t(_);
				}
			},
			u = (n) => (n.done ? w(n.value) : Promise.resolve(n.value).then(d, c));
		u((m = m.apply(R, h)).next());
	});
import {
	v as z,
	L as A,
	o as b,
	e as I,
	w as i,
	f as l,
	h as r,
	I as P,
	g as $,
	U as G,
	i as C,
	F as U,
	t as y,
	z as D,
	Q as H,
	l as O,
	B as g,
	a as J,
	b as Q,
} from "./frappe-ui-CXkWuvNK.js";
import { a as X, _ as E, b as Y } from "./SectionCard-BKeIA1B1.js";
import { _ as q } from "./DashGrid-CcXWxztj.js";
import { _ as K } from "./DataTable-KquPBl5L.js";
import { _ as W } from "./StatTiles-knaJnTjR.js";
import { _ as Z } from "./StatusBadge-DcMGXIA6.js";
import { _ as N } from "./FieldRow-2cmCHPuL.js";
import { _ as T } from "./DateField-BLUeL_2-.js";
import { p as v, d as V, b as x } from "./index-BpEXs0_U.js";
import { n as ee, a as B, e as M } from "./toast-Ca-cKV9o.js";
import "./EmptyState-DhAxAin0.js";
const ae = { class: "flex flex-wrap items-center gap-2" },
	le = { key: 1, class: "text-base text-ink-gray-5" },
	te = { class: "font-semibold text-ink-gray-9" },
	oe = { class: "flex flex-col" },
	ve = {
		__name: "Payslips",
		setup(R) {
			const h = [
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
				w = Q(),
				t = J(() => v.data),
				d = g("12m"),
				c = g(""),
				u = g(""),
				n = g(!1);
			function _() {
				(d.value === "custom" && !(c.value && u.value)) ||
					v.fetch({
						period: d.value,
						from_date: c.value || void 0,
						to_date: u.value || void 0,
					});
			}
			z([d, c, u], _);
			function S(s, a) {
				const o = URL.createObjectURL(s),
					p = document.createElement("a");
				(p.href = o), (p.download = a), p.click(), URL.revokeObjectURL(o);
			}
			function F(s) {
				return k(this, null, function* () {
					try {
						const a = yield fetch(
							`/api/method/hrms.api.portal.payslip_pdf?name=${encodeURIComponent(
								s.name,
							)}`,
						);
						if (!a.ok) throw new Error(yield a.text());
						S(yield a.blob(), `${s.period.replace(" ", "-")}-payslip.pdf`);
					} catch (a) {
						B("Could not download", M(a, "Try again in a moment."));
					}
				});
			}
			function L(s) {
				w.push(`/payslips/${encodeURIComponent(s.name)}`);
			}
			function j() {
				return k(this, null, function* () {
					var a;
					const s = (((a = t.value) == null ? void 0 : a.slips) || []).map(
						(o) => o.name,
					);
					if (s.length) {
						n.value = !0;
						try {
							const o = yield fetch("/api/method/hrms.api.portal.payslips_zip", {
								method: "POST",
								headers: {
									"Content-Type": "application/json",
									Accept: "application/json",
									"X-Frappe-CSRF-Token": window.csrf_token,
								},
								body: JSON.stringify({ names: s }),
							});
							if (!o.ok) throw new Error(yield o.text());
							S(yield o.blob(), "payslips.zip"),
								ee(`${s.length} payslips downloaded`);
						} catch (o) {
							B("Could not download", M(o, "Try again in a moment."));
						} finally {
							n.value = !1;
						}
					}
				});
			}
			return (
				A(() => v.fetch()),
				(s, a) => (
					b(),
					I(
						Y,
						{ loading: r(v).loading && !r(v).data },
						{
							default: i(() => {
								var o, p;
								return [
									l(
										X,
										{ title: "Payslips", subtitle: "Your salary history" },
										{
											actions: i(() => {
												var e, f;
												return [
													l(
														r(P),
														{
															variant: "subtle",
															"icon-left": "lucide-download",
															disabled: !(
																(f =
																	(e = t.value) == null
																		? void 0
																		: e.slips) != null &&
																f.length
															),
															loading: n.value,
															label: "Download All",
															onClick: j,
														},
														null,
														8,
														["disabled", "loading"],
													),
												];
											}),
											_: 1,
										},
									),
									$("div", ae, [
										l(
											r(G),
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
											  C(
													U,
													{ key: 0 },
													[
														l(
															T,
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
														l(
															T,
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
											: (p = (o = t.value) == null ? void 0 : o.range) !=
														null && p.from_date
											  ? (b(),
											    C(
														"span",
														le,
														y(r(V)(t.value.range.from_date)) +
															" to " +
															y(r(V)(t.value.range.to_date)),
														1,
											    ))
											  : D("", !0),
									]),
									t.value
										? (b(),
										  C(
												U,
												{ key: 0 },
												[
													l(W, { tiles: s.tiles }, null, 8, ["tiles"]),
													l(q, null, {
														main: i(() => [
															l(
																E,
																{
																	title: "Monthly Payslips",
																	padded: !1,
																},
																{
																	default: i(() => [
																		l(
																			K,
																			{
																				columns: h,
																				rows: t.value
																					.slips,
																				clickable: "",
																				"empty-message":
																					"No payslips in this period.",
																				onRowClick: L,
																			},
																			{
																				"cell-gross_pay":
																					i(
																						({
																							row: e,
																						}) => [
																							O(
																								y(
																									r(
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
																					i(
																						({
																							row: e,
																						}) => [
																							O(
																								y(
																									r(
																										x,
																									)(
																										e.total_deduction,
																									),
																								),
																								1,
																							),
																						],
																					),
																				"cell-net_pay": i(
																					({
																						row: e,
																					}) => [
																						$(
																							"span",
																							te,
																							y(
																								r(
																									x,
																								)(
																									e.net_pay,
																								),
																							),
																							1,
																						),
																					],
																				),
																				"cell-status": i(
																					({
																						row: e,
																					}) => [
																						l(
																							Z,
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
																				"cell-download": i(
																					({
																						row: e,
																					}) => [
																						l(
																							r(P),
																							{
																								variant:
																									"ghost",
																								icon: "lucide-download",
																								label: `Download ${e.period}`,
																								onClick:
																									H(
																										(
																											f,
																										) =>
																											F(
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
														side: i(() => [
															l(
																E,
																{
																	title: "Salary Structure",
																	"readonly-label": "HR-owned",
																},
																{
																	default: i(() => {
																		var e, f;
																		return [
																			$("dl", oe, [
																				l(
																					N,
																					{
																						label: "Structure",
																						value:
																							(e =
																								t
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
																				l(
																					N,
																					{
																						label: "Effective",
																						value:
																							(f =
																								t
																									.value
																									.structure) !=
																								null &&
																							f.from_date
																								? r(
																										V,
																								  )(
																										t
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
										: D("", !0),
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
export { ve as default };
