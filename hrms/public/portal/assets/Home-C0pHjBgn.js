var D = (d, b, l) =>
	new Promise((a, g) => {
		var _ = (t) => {
				try {
					m(l.next(t));
				} catch (c) {
					g(c);
				}
			},
			f = (t) => {
				try {
					m(l.throw(t));
				} catch (c) {
					g(c);
				}
			},
			m = (t) => (t.done ? a(t.value) : Promise.resolve(t.value).then(_, f));
		m((l = l.apply(d, b)).next());
	});
import { _ as $, a as V, b as E } from "./SectionCard-C5Qs8pBJ.js";
import { _ as z } from "./DataTable-BPI_hH2T.js";
import { _ as O } from "./StatusBadge-sSVuNJEI.js";
import { _ as I } from "./PersonRow-2k8WhDWN.js";
import { _ as F } from "./FieldRow-DoxIhPye.js";
import { _ as T } from "./EmptyState-38_uLDf3.js";
import {
	e as G,
	m as H,
	s as U,
	t as P,
	h as x,
	d as Y,
	a as W,
	b as J,
	c as j,
} from "./index-BSaIzYPn.js";
import { n as K, a as Q, e as X } from "./toast-BPVivXt-.js";
import {
	L as R,
	M as Z,
	o as n,
	d as y,
	w as i,
	e as s,
	t as u,
	f as o,
	h as r,
	z as L,
	g as h,
	I as A,
	k as q,
	F as v,
	i as C,
	s as S,
	a as w,
	B,
	q as ee,
} from "./frappe-ui-D0k6koYp.js";
const te = { class: "flex flex-wrap items-start justify-between gap-3" },
	ae = { class: "min-w-0" },
	se = { class: "text-base text-ink-gray-5" },
	ne = { class: "nums mt-0.5 text-4xl-semibold leading-tight text-ink-gray-9" },
	le = { class: "mt-1.5 flex flex-wrap items-center gap-2" },
	ie = { key: 0, class: "text-base text-ink-gray-5" },
	oe = { class: "flex shrink-0 gap-2" },
	ce = { class: "grid grid-cols-7 gap-1.5" },
	re = { class: "text-[10px] text-ink-gray-4" },
	ue = ["title"],
	de = {
		__name: "CheckInCard",
		props: {
			checkin: { type: Object, default: () => ({}) },
			week: { type: Array, default: () => [] },
		},
		emits: ["changed"],
		setup(d, { emit: b }) {
			const l = d,
				a = b,
				g = B("00:00:00"),
				_ = B(!1);
			let f = null;
			const m = w(() => {
					const e = U(l.checkin.shift);
					return l.checkin.shift ? `${l.checkin.shift.name}, ${e}` : null;
				}),
				t = w(() =>
					l.checkin.checked_in
						? `Checked in at ${P(l.checkin.since)}`
						: "You have not checked in today",
				);
			function c() {
				g.value = l.checkin.checked_in ? G(l.checkin.since) : "00:00:00";
			}
			function p() {
				return D(this, null, function* () {
					_.value = !0;
					try {
						yield H.submit({ log_type: l.checkin.checked_in ? "OUT" : "IN" }),
							K(l.checkin.checked_in ? "Checked out" : "Checked in"),
							a("changed");
					} catch (e) {
						Q("Could not record that", X(e, "Try again in a moment."));
					} finally {
						_.value = !1;
					}
				});
			}
			function M(e) {
				switch (e.status) {
					case "Present":
					case "Work From Home":
						return "bg-surface-green-2";
					case "Half Day":
						return "bg-surface-amber-2";
					case "On Leave":
						return "bg-surface-blue-2";
					case "Absent":
						return "bg-surface-red-2";
					default:
						return "bg-surface-gray-3";
				}
			}
			return (
				R(() => {
					c(), (f = setInterval(c, 1e3));
				}),
				Z(() => clearInterval(f)),
				(e, N) => (
					n(),
					y($, null, {
						default: i(() => [
							s("div", te, [
								s("div", ae, [
									s("p", se, u(t.value), 1),
									s("p", ne, u(d.checkin.checked_in ? g.value : "—"), 1),
									s("div", le, [
										o(
											O,
											{
												status: d.checkin.checked_in
													? "On shift"
													: "Not checked in",
												label: d.checkin.checked_in
													? "On shift"
													: "Not checked in",
											},
											null,
											8,
											["status", "label"],
										),
										m.value ? (n(), r("span", ie, u(m.value), 1)) : L("", !0),
									]),
								]),
								s("div", oe, [
									o(
										h(A),
										{
											variant: "subtle",
											onClick:
												N[0] ||
												(N[0] = (k) => e.$router.push("/attendance")),
										},
										{
											default: i(() => [
												...(N[1] || (N[1] = [q("View Log", -1)])),
											]),
											_: 1,
										},
									),
									o(
										h(A),
										{ variant: "solid", loading: _.value, onClick: p },
										{
											default: i(() => [
												q(
													u(
														d.checkin.checked_in
															? "Check Out"
															: "Check In",
													),
													1,
												),
											]),
											_: 1,
										},
										8,
										["loading"],
									),
								]),
							]),
							s("div", ce, [
								(n(!0),
								r(
									v,
									null,
									C(
										d.week,
										(k) => (
											n(),
											r(
												"div",
												{
													key: k.date,
													class: "flex flex-col items-center gap-1",
												},
												[
													s("span", re, u(k.label), 1),
													s(
														"span",
														{
															class: S([
																"h-6 w-full rounded-4",
																[
																	M(k),
																	k.is_today &&
																		"ring-1 ring-inset ring-outline-gray-4",
																],
															]),
															title: k.status || "Not marked",
														},
														null,
														10,
														ue,
													),
												],
											)
										),
									),
									128,
								)),
							]),
						]),
						_: 1,
					})
				)
			);
		},
	},
	me = { class: "grid grid-cols-2 gap-3 sm:grid-cols-3" },
	ge = {
		class: "flex h-7 w-7 shrink-0 items-center justify-center rounded-4 bg-surface-gray-3 text-ink-gray-7",
	},
	_e = { class: "text-base leading-tight text-ink-gray-8" },
	he = { class: "flex flex-col gap-2.5" },
	fe = { class: "text-ink-gray-8" },
	pe = { class: "nums text-ink-gray-5" },
	ke = { class: "text-ink-gray-6" },
	ye = { class: "text-base text-ink-gray-5" },
	ve = { key: 0, class: "flex flex-col gap-2" },
	be = { key: 0, class: "flex flex-col" },
	Ie = {
		__name: "Home",
		setup(d) {
			const b = [
					{ label: "Apply Leave", to: "/leave", icon: "lucide-sunrise" },
					{ label: "Claim Expense", to: "/expenses", icon: "lucide-credit-card" },
					{ label: "Latest Payslip", to: "/payslips", icon: "lucide-file-text" },
					{ label: "Request Advance", to: "/advances", icon: "lucide-trending-up" },
					{ label: "Regularise", to: "/attendance", icon: "lucide-clock" },
				],
				l = [
					{ key: "type", label: "Type", hideOnMobile: !0 },
					{ key: "detail", label: "Detail", primary: !0 },
					{ key: "submitted", label: "Submitted", nums: !0, muted: !0 },
					{ key: "approver", label: "Approver" },
					{ key: "status", label: "Status", align: "right", badge: !0 },
				],
				a = w(() => x.data);
			function g(t) {
				if (t.type === "Expense") return W(t.amount);
				const c = J(t.from_date, t.to_date);
				return t.label ? `${t.label}, ${c}` : c;
			}
			const _ = w(() => {
					var p;
					const t = j().hour();
					return `${
						t < 12 ? "Good morning" : t < 17 ? "Good afternoon" : "Good evening"
					}, ${((p = a.value) == null ? void 0 : p.greeting_name) || ""}`
						.trim()
						.replace(/,$/, "");
				}),
				f = w(() => {
					var t;
					return Y((t = a.value) == null ? void 0 : t.today, "dddd, D MMMM YYYY");
				});
			function m(t) {
				return j(t).format("D MMM");
			}
			return (
				R(() => x.fetch()),
				(t, c) => {
					const p = ee("RouterLink");
					return (
						n(),
						y(
							E,
							{ loading: h(x).loading && !h(x).data },
							{
								default: i(() => {
									var M;
									return [
										o(V, { title: _.value, subtitle: f.value }, null, 8, [
											"title",
											"subtitle",
										]),
										a.value
											? (n(),
											  r(
													v,
													{ key: 0 },
													[
														o(
															de,
															{
																checkin: a.value.checkin,
																week: a.value.week,
																onChanged:
																	c[0] ||
																	(c[0] = (e) => h(x).reload()),
															},
															null,
															8,
															["checkin", "week"],
														),
														s("div", me, [
															(n(),
															r(
																v,
																null,
																C(b, (e) =>
																	o(
																		p,
																		{
																			key: e.label,
																			to: e.to,
																			class: "flex items-center gap-2.5 rounded-6 border border-outline-gray-1 bg-surface-base p-3 transition-colors hover:bg-surface-gray-1",
																		},
																		{
																			default: i(() => [
																				s("span", ge, [
																					s(
																						"span",
																						{
																							class: S(
																								[
																									e.icon,
																									"h-3.5 w-3.5",
																								],
																							),
																							"aria-hidden":
																								"true",
																						},
																						null,
																						2,
																					),
																				]),
																				s(
																					"span",
																					_e,
																					u(e.label),
																					1,
																				),
																			]),
																			_: 2,
																		},
																		1032,
																		["to"],
																	),
																),
																64,
															)),
														]),
														(M = a.value.pending_approvals) != null &&
														M.length
															? (n(),
															  y(
																	$,
																	{
																		key: 0,
																		title: "Waiting on You",
																	},
																	{
																		action: i(() => [
																			o(
																				O,
																				{
																					status: "pending",
																					label: String(
																						a.value
																							.pending_approvals
																							.length,
																					),
																				},
																				null,
																				8,
																				["label"],
																			),
																		]),
																		default: i(() => [
																			s("ul", he, [
																				(n(!0),
																				r(
																					v,
																					null,
																					C(
																						a.value
																							.pending_approvals,
																						(e) => (
																							n(),
																							r(
																								"li",
																								{
																									key: e.name,
																									class: "flex items-center justify-between gap-2",
																								},
																								[
																									o(
																										I,
																										{
																											name: e.employee_name,
																											meta: `${e.type}, ${e.detail}`,
																											size: "md",
																										},
																										null,
																										8,
																										[
																											"name",
																											"meta",
																										],
																									),
																									c[1] ||
																										(c[1] =
																											s(
																												"span",
																												{
																													class: "h-3.5 w-3.5 shrink-0 text-ink-gray-4 lucide-chevron-right",
																													"aria-hidden":
																														"true",
																												},
																												null,
																												-1,
																											)),
																								],
																							)
																						),
																					),
																					128,
																				)),
																			]),
																		]),
																		_: 1,
																	},
															  ))
															: L("", !0),
														o(
															$,
															{ title: "My Requests", padded: !1 },
															{
																action: i(() => [
																	o(h(A), {
																		variant: "ghost",
																		route: "/leave",
																		label: "View All",
																	}),
																]),
																default: i(() => [
																	o(
																		z,
																		{
																			columns: l,
																			rows: a.value.requests,
																			"empty-message":
																				"You have not raised any requests yet.",
																		},
																		{
																			"cell-detail": i(
																				({ row: e }) => [
																					s(
																						"span",
																						fe,
																						u(g(e)),
																						1,
																					),
																				],
																			),
																			"cell-submitted": i(
																				({ row: e }) => [
																					s(
																						"span",
																						pe,
																						u(
																							h(Y)(
																								e.submitted,
																							),
																						),
																						1,
																					),
																				],
																			),
																			"cell-approver": i(
																				({ row: e }) => [
																					s(
																						"span",
																						ke,
																						u(
																							e.approver_name ||
																								"—",
																						),
																						1,
																					),
																				],
																			),
																			"cell-status": i(
																				({ row: e }) => [
																					o(
																						O,
																						{
																							status: e.status,
																						},
																						null,
																						8,
																						["status"],
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
														o(
															$,
															{ title: "Out Today" },
															{
																action: i(() => [
																	s(
																		"span",
																		ye,
																		u(
																			a.value.out_today
																				.count,
																		) +
																			" of " +
																			u(
																				a.value.out_today
																					.total,
																			),
																		1,
																	),
																]),
																default: i(() => [
																	a.value.out_today.people.length
																		? (n(),
																		  r("ul", ve, [
																				(n(!0),
																				r(
																					v,
																					null,
																					C(
																						a.value
																							.out_today
																							.people,
																						(e) => (
																							n(),
																							r(
																								"li",
																								{
																									key: e.employee,
																									class: "flex items-center justify-between gap-2",
																								},
																								[
																									o(
																										I,
																										{
																											name: e.employee_name,
																											to: `/directory/${e.employee}`,
																											size: "md",
																										},
																										null,
																										8,
																										[
																											"name",
																											"to",
																										],
																									),
																									o(
																										O,
																										{
																											status: "on leave",
																											label: e.reason,
																										},
																										null,
																										8,
																										[
																											"label",
																										],
																									),
																								],
																							)
																						),
																					),
																					128,
																				)),
																		  ]))
																		: (n(),
																		  y(T, {
																				key: 1,
																				message:
																					"Everybody is in today.",
																		  })),
																]),
																_: 1,
															},
														),
														o(
															$,
															{ title: "Coming Up" },
															{
																default: i(() => [
																	a.value.coming_up.length
																		? (n(),
																		  r("dl", be, [
																				(n(!0),
																				r(
																					v,
																					null,
																					C(
																						a.value
																							.coming_up,
																						(e) => (
																							n(),
																							y(
																								F,
																								{
																									key:
																										e.date +
																										e.label,
																									label: m(
																										e.date,
																									),
																									value: e.label,
																								},
																								null,
																								8,
																								[
																									"label",
																									"value",
																								],
																							)
																						),
																					),
																					128,
																				)),
																		  ]))
																		: (n(),
																		  y(T, {
																				key: 1,
																				message:
																					"Nothing in the next 60 days.",
																		  })),
																]),
																_: 1,
															},
														),
													],
													64,
											  ))
											: L("", !0),
									];
								}),
								_: 1,
							},
							8,
							["loading"],
						)
					);
				}
			);
		},
	};
export { Ie as default };
