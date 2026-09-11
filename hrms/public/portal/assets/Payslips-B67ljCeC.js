var k = (R, b, m) =>
	new Promise((w, l) => {
		var d = (n) => {
				try {
					u(m.next(n));
				} catch (_) {
					l(_);
				}
			},
			c = (n) => {
				try {
					u(m.throw(n));
				} catch (_) {
					l(_);
				}
			},
			u = (n) => (n.done ? w(n.value) : Promise.resolve(n.value).then(d, c));
		u((m = m.apply(R, b)).next());
	});
import {
	v as A,
	L as G,
	o as g,
	d as H,
	w as i,
	f as t,
	g as r,
	I as U,
	e as $,
	U as J,
	h as C,
	F as O,
	t as y,
	z as E,
	Q,
	k as N,
	B as h,
	a as X,
	b as Y,
} from "./frappe-ui-rHlwnvVy.js";
import { a as q, _ as T, b as K } from "./SectionCard-0tgyDAFI.js";
import { _ as W } from "./DashGrid-Cmnm2mAO.js";
import { _ as Z } from "./DataTable-BY05XQx8.js";
import { _ as ee } from "./StatTiles-DcUJsMoQ.js";
import { _ as ae } from "./StatusBadge-ZWn2FvVw.js";
import { _ as B } from "./FieldRow-C13lI4HG.js";
import { _ as M } from "./DateField-c9rL8vfk.js";
import { p as v, d as V, a as x } from "./index-6wvshjQq.js";
import { n as le, a as F, e as L } from "./toast-BxUFHbEO.js";
import "./EmptyState-0_BFjfJU.js";
const te = { class: "flex flex-wrap items-center gap-2" },
	oe = { key: 1, class: "text-base text-ink-gray-5" },
	se = { class: "font-semibold text-ink-gray-9" },
	ne = { class: "flex flex-col" },
	he = {
		__name: "Payslips",
		setup(R) {
			const b = [
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
				w = Y(),
				l = X(() => v.data),
				d = h("12m"),
				c = h(""),
				u = h(""),
				n = h(!1);
			function _() {
				(d.value === "custom" && !(c.value && u.value)) ||
					v.fetch({
						period: d.value,
						from_date: c.value || void 0,
						to_date: u.value || void 0,
					});
			}
			A([d, c, u], _);
			function S(s, a) {
				const o = URL.createObjectURL(s),
					p = document.createElement("a");
				(p.href = o), (p.download = a), p.click(), URL.revokeObjectURL(o);
			}
			function j(s) {
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
						F("Could not download", L(a, "Try again in a moment."));
					}
				});
			}
			function z(s) {
				w.push(`/payslips/${encodeURIComponent(s.name)}`);
			}
			function I() {
				return k(this, null, function* () {
					var a;
					const s = (((a = l.value) == null ? void 0 : a.slips) || []).map(
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
								le(`${s.length} payslips downloaded`);
						} catch (o) {
							F("Could not download", L(o, "Try again in a moment."));
						} finally {
							n.value = !1;
						}
					}
				});
			}
			return (
				G(() => v.fetch()),
				(s, a) => (
					g(),
					H(
						K,
						{ loading: r(v).loading && !r(v).data },
						{
							default: i(() => {
								var o, p;
								return [
									t(
										q,
										{ title: "Payslips", subtitle: "Your salary history" },
										{
											actions: i(() => {
												var e, f, D, P;
												return [
													t(
														r(U),
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
															loading: n.value,
															label:
																(P =
																	(D = l.value) == null
																		? void 0
																		: D.slips) != null &&
																P.length
																	? `Download ${l.value.slips.length}`
																	: "Download",
															onClick: I,
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
									$("div", te, [
										t(
											r(J),
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
											? (g(),
											  C(
													O,
													{ key: 0 },
													[
														t(
															M,
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
															M,
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
											: (p = (o = l.value) == null ? void 0 : o.range) !=
														null && p.from_date
											  ? (g(),
											    C(
														"span",
														oe,
														y(r(V)(l.value.range.from_date)) +
															" to " +
															y(r(V)(l.value.range.to_date)),
														1,
											    ))
											  : E("", !0),
									]),
									l.value
										? (g(),
										  C(
												O,
												{ key: 0 },
												[
													t(ee, { tiles: s.tiles }, null, 8, ["tiles"]),
													t(W, null, {
														main: i(() => [
															t(
																T,
																{
																	title: "Monthly Payslips",
																	padded: !1,
																},
																{
																	default: i(() => [
																		t(
																			Z,
																			{
																				columns: b,
																				rows: l.value
																					.slips,
																				clickable: "",
																				"empty-message":
																					"No payslips in this period.",
																				onRowClick: z,
																			},
																			{
																				"cell-gross_pay":
																					i(
																						({
																							row: e,
																						}) => [
																							N(
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
																							N(
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
																							se,
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
																						t(
																							ae,
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
																						t(
																							r(U),
																							{
																								variant:
																									"ghost",
																								icon: "lucide-download",
																								label: `Download ${e.period}`,
																								onClick:
																									Q(
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
														side: i(() => [
															t(
																T,
																{
																	title: "Salary Structure",
																	"readonly-label": "HR-owned",
																},
																{
																	default: i(() => {
																		var e, f;
																		return [
																			$("dl", ne, [
																				t(
																					B,
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
																					B,
																					{
																						label: "Effective",
																						value:
																							(f =
																								l
																									.value
																									.structure) !=
																								null &&
																							f.from_date
																								? r(
																										V,
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
										: E("", !0),
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
