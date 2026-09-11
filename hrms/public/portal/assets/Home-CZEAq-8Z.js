var V = (y, L, c) =>
	new Promise((T, s) => {
		var x = (m) => {
				try {
					v(c.next(m));
				} catch (o) {
					s(o);
				}
			},
			p = (m) => {
				try {
					v(c.throw(m));
				} catch (o) {
					s(o);
				}
			},
			v = (m) => (m.done ? T(m.value) : Promise.resolve(m.value).then(x, p));
		v((c = c.apply(y, L)).next());
	});
import { _ as N, a as te, b as ae } from "./SectionCard-0tgyDAFI.js";
import { _ as z } from "./DataTable-BY05XQx8.js";
import { _ as M } from "./StatusBadge-ZWn2FvVw.js";
import { _ as U } from "./PersonRow-LB2-2vnj.js";
import { _ as se } from "./FieldRow-C13lI4HG.js";
import { _ as W } from "./EmptyState-0_BFjfJU.js";
import {
	d as D,
	t as Y,
	e as ne,
	m as le,
	s as F,
	h as A,
	a as ie,
	b as oe,
	c as G,
} from "./index-6wvshjQq.js";
import { n as re, a as ue, e as ce } from "./toast-BxUFHbEO.js";
import {
	L as P,
	M as de,
	o as n,
	d as w,
	w as r,
	e as a,
	t as i,
	f as u,
	h as d,
	z as I,
	g as f,
	I as q,
	k as K,
	F as b,
	i as C,
	s as j,
	a as k,
	B as S,
	N as ge,
	O as me,
	q as fe,
} from "./frappe-ui-rHlwnvVy.js";
const _e = { class: "flex flex-wrap items-start justify-between gap-3" },
	he = { class: "min-w-0" },
	pe = { class: "text-base text-ink-gray-5" },
	ye = { class: "nums mt-0.5 text-4xl-semibold leading-tight text-ink-gray-9" },
	ke = { class: "mt-1.5 flex flex-wrap items-center gap-2" },
	ve = { key: 0, class: "text-base text-ink-gray-5" },
	be = { class: "flex shrink-0 gap-2" },
	xe = ["title", "tabindex", "aria-pressed", "aria-label", "onClick"],
	$e = { class: "text-[10px] text-ink-gray-4" },
	we = { key: 0, class: "rounded-6 border border-outline-gray-1 bg-surface-gray-1 px-3 py-2.5" },
	Me = { class: "flex flex-wrap items-center justify-between gap-2" },
	Ce = { class: "flex min-w-0 flex-wrap items-center gap-2" },
	Oe = { class: "text-base-semibold text-ink-gray-8" },
	Ne = { key: 0, class: "truncate text-base text-ink-gray-5" },
	De = { class: "mt-2 grid grid-cols-2 gap-x-4 gap-y-2 sm:grid-cols-4" },
	Ie = { class: "text-sm text-ink-gray-5" },
	Le = ["title"],
	Te = { class: "mt-2.5 border-t border-outline-gray-1 pt-2.5" },
	Ae = { key: 0, class: "mt-1.5 flex flex-wrap gap-1.5" },
	Se = { class: "text-sm text-ink-gray-6" },
	je = { class: "nums text-sm text-ink-gray-8" },
	Re = { key: 1, class: "mt-1 text-base text-ink-gray-5" },
	Ye = {
		__name: "CheckInCard",
		props: {
			checkin: { type: Object, default: () => ({}) },
			week: { type: Array, default: () => [] },
		},
		emits: ["changed"],
		setup(y, { emit: L }) {
			const c = y,
				T = L,
				s = S("00:00:00"),
				x = S(!1),
				p = S(null),
				v = S([]),
				m = S(null);
			let o = null;
			const h = k(() => {
					const t = F(c.checkin.shift);
					return c.checkin.shift ? `${c.checkin.shift.name}, ${t}` : null;
				}),
				O = k(() =>
					c.checkin.checked_in
						? `Checked in at ${Y(c.checkin.since)}`
						: "You have not checked in today",
				),
				_ = k(() => c.week.find((t) => t.date === p.value) || null),
				e = k(() => {
					if (m.value !== null) return m.value;
					const t = c.week.findIndex((g) => g.is_today);
					return t === -1 ? 0 : t;
				});
			function R(t) {
				return t.status
					? t.status
					: t.weekly_off
					  ? "Weekly off"
					  : t.holiday
					    ? "Holiday"
					    : t.is_future
					      ? "Upcoming"
					      : "Not marked";
			}
			const E = k(() => {
					var t, g;
					return (
						((t = _.value) == null ? void 0 : t.leave_type) ||
						((g = _.value) == null ? void 0 : g.holiday) ||
						""
					);
				}),
				J = k(() => {
					const t = _.value;
					return t
						? [
								{ label: "In", value: Y(t.in_time) },
								{ label: "Out", value: Y(t.out_time) },
								{ label: "Hours", value: t.hours ? `${t.hours} h` : "—" },
								{
									label: "Shift",
									value: t.shift ? `${t.shift.name}, ${F(t.shift)}` : "—",
								},
						  ]
						: [];
				});
			function Q(t) {
				p.value = p.value === t.date ? null : t.date;
			}
			function X(t) {
				const g = { ArrowLeft: -1, ArrowRight: 1 }[t.key];
				let $;
				if (g) $ = e.value + g;
				else if (t.key === "Home") $ = 0;
				else if (t.key === "End") $ = c.week.length - 1;
				else return;
				t.preventDefault(),
					(m.value = Math.max(0, Math.min(c.week.length - 1, $))),
					ge(() => {
						var l;
						return (l = v.value[m.value]) == null ? void 0 : l.focus();
					});
			}
			function H() {
				s.value = c.checkin.checked_in ? ne(c.checkin.since) : "00:00:00";
			}
			function Z() {
				return V(this, null, function* () {
					x.value = !0;
					try {
						yield le.submit({ log_type: c.checkin.checked_in ? "OUT" : "IN" }),
							re(c.checkin.checked_in ? "Checked out" : "Checked in"),
							T("changed");
					} catch (t) {
						ue("Could not record that", ce(t, "Try again in a moment."));
					} finally {
						x.value = !1;
					}
				});
			}
			function ee(t) {
				switch (t.status) {
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
				P(() => {
					H(), (o = setInterval(H, 1e3));
				}),
				de(() => clearInterval(o)),
				(t, g) => (
					n(),
					w(N, null, {
						default: r(() => {
							var $;
							return [
								a("div", _e, [
									a("div", he, [
										a("p", pe, i(O.value), 1),
										a("p", ye, i(y.checkin.checked_in ? s.value : "—"), 1),
										a("div", ke, [
											u(
												M,
												{
													status: y.checkin.checked_in
														? "On shift"
														: "Not checked in",
													label: y.checkin.checked_in
														? "On shift"
														: "Not checked in",
												},
												null,
												8,
												["status", "label"],
											),
											h.value
												? (n(), d("span", ve, i(h.value), 1))
												: I("", !0),
										]),
									]),
									a("div", be, [
										u(
											f(q),
											{
												variant: "subtle",
												onClick:
													g[0] ||
													(g[0] = (l) => t.$router.push("/attendance")),
											},
											{
												default: r(() => [
													...(g[2] || (g[2] = [K("View Log", -1)])),
												]),
												_: 1,
											},
										),
										u(
											f(q),
											{ variant: "solid", loading: x.value, onClick: Z },
											{
												default: r(() => [
													K(
														i(
															y.checkin.checked_in
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
								a(
									"div",
									{
										class: "grid grid-cols-7 gap-1.5",
										role: "toolbar",
										"aria-label": "This week",
										onKeydown: X,
									},
									[
										(n(!0),
										d(
											b,
											null,
											C(
												y.week,
												(l, B) => (
													n(),
													d(
														"button",
														{
															key: l.date,
															ref_for: !0,
															ref_key: "pills",
															ref: v,
															type: "button",
															title: `${f(D)(
																l.date,
																"dddd D MMMM",
															)}, ${R(l)}`,
															class: "flex cursor-pointer flex-col items-center gap-1 rounded-4 p-1 transition-colors hover:bg-surface-gray-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3",
															tabindex: B === e.value ? 0 : -1,
															"aria-pressed": p.value === l.date,
															"aria-label": `${f(D)(
																l.date,
																"dddd D MMMM",
															)}, ${R(l)}`,
															onClick: (Xe) => Q(l),
														},
														[
															a("span", $e, i(l.label), 1),
															a(
																"span",
																{
																	class: j([
																		"h-6 w-full rounded-4",
																		[
																			ee(l),
																			l.is_today &&
																				"ring-1 ring-inset ring-outline-gray-4",
																		],
																	]),
																},
																null,
																2,
															),
															a(
																"span",
																{
																	class: j([
																		"-mb-1 h-px w-full transition-colors",
																		p.value === l.date
																			? "bg-[var(--outline-gray-8)]"
																			: "bg-transparent",
																	]),
																	"aria-hidden": "true",
																},
																null,
																2,
															),
														],
														8,
														xe,
													)
												),
											),
											128,
										)),
									],
									32,
								),
								_.value
									? (n(),
									  d("div", we, [
											a("div", Me, [
												a("div", Ce, [
													a(
														"span",
														Oe,
														i(f(D)(_.value.date, "dddd, D MMMM")),
														1,
													),
													u(
														M,
														{ status: R(_.value), label: R(_.value) },
														null,
														8,
														["status", "label"],
													),
													E.value
														? (n(), d("span", Ne, i(E.value), 1))
														: I("", !0),
												]),
												u(f(q), {
													variant: "ghost",
													icon: "lucide-x",
													label: "Close day",
													onClick:
														g[1] || (g[1] = (l) => (p.value = null)),
												}),
											]),
											a("dl", De, [
												(n(!0),
												d(
													b,
													null,
													C(
														J.value,
														(l) => (
															n(),
															d("div", { key: l.label }, [
																a("dt", Ie, i(l.label), 1),
																a(
																	"dd",
																	{
																		class: "nums truncate text-base text-ink-gray-8",
																		title: l.value,
																	},
																	i(l.value),
																	9,
																	Le,
																),
															])
														),
													),
													128,
												)),
											]),
											a("div", Te, [
												g[3] ||
													(g[3] = a(
														"p",
														{ class: "text-sm text-ink-gray-5" },
														"Check-ins",
														-1,
													)),
												($ = _.value.logs) != null && $.length
													? (n(),
													  d("ul", Ae, [
															(n(!0),
															d(
																b,
																null,
																C(
																	_.value.logs,
																	(l, B) => (
																		n(),
																		d(
																			"li",
																			{
																				key: B,
																				class: "flex items-center gap-1.5 rounded-full border border-outline-gray-1 bg-surface-base py-0.5 pl-1.5 pr-2.5",
																			},
																			[
																				a(
																					"span",
																					{
																						class: j([
																							"h-1.5 w-1.5 rounded-full",
																							l.log_type ===
																							"IN"
																								? "bg-surface-green-3"
																								: "bg-surface-gray-5",
																						]),
																						"aria-hidden":
																							"true",
																					},
																					null,
																					2,
																				),
																				a(
																					"span",
																					Se,
																					i(l.log_type),
																					1,
																				),
																				a(
																					"span",
																					je,
																					i(
																						f(Y)(
																							l.time,
																						),
																					),
																					1,
																				),
																			],
																		)
																	),
																),
																128,
															)),
													  ]))
													: (n(),
													  d(
															"p",
															Re,
															i(
																_.value.is_future
																	? "Nothing recorded yet."
																	: "No check-ins on this day.",
															),
															1,
													  )),
											]),
									  ]))
									: I("", !0),
							];
						}),
						_: 1,
					})
				)
			);
		},
	},
	qe = { class: "flex items-center gap-2.5" },
	Be = { class: "nums text-base text-ink-gray-5" },
	Ee = { class: "text-ink-gray-8" },
	He = { class: "nums text-ink-gray-5" },
	Ve = { class: "grid grid-cols-2 gap-3 sm:grid-cols-3" },
	ze = {
		class: "flex h-7 w-7 shrink-0 items-center justify-center rounded-4 bg-surface-gray-3 text-ink-gray-7",
	},
	Ue = { class: "text-base leading-tight text-ink-gray-8" },
	We = { class: "flex flex-col gap-2.5" },
	Fe = { class: "text-ink-gray-8" },
	Ge = { class: "nums text-ink-gray-5" },
	Ke = { class: "text-ink-gray-6" },
	Pe = { class: "text-base text-ink-gray-5" },
	Je = { key: 0, class: "flex flex-col gap-2" },
	Qe = { key: 0, class: "flex flex-col" },
	ut = {
		__name: "Home",
		setup(y) {
			const L = [
					{ key: "activity", label: "Task", primary: !0 },
					{ key: "owner", label: "With", muted: !0, hideOnMobile: !0 },
					{ key: "due", label: "Due", align: "right", nums: !0, hideOnMobile: !0 },
					{ key: "status", label: "Status", align: "right", badge: !0 },
				],
				c = [
					{ label: "Apply Leave", to: "/leave", icon: "lucide-sunrise" },
					{ label: "Claim Expense", to: "/expenses", icon: "lucide-credit-card" },
					{ label: "Latest Payslips", to: "/payslips", icon: "lucide-file-text" },
					{ label: "Request Advance", to: "/advances", icon: "lucide-trending-up" },
					{ label: "Regularise", to: "/attendance", icon: "lucide-clock" },
				],
				T = [
					{ key: "type", label: "Type", hideOnMobile: !0 },
					{ key: "detail", label: "Detail", primary: !0 },
					{ key: "submitted", label: "Submitted", nums: !0, muted: !0 },
					{ key: "approver", label: "Approver" },
					{ key: "status", label: "Status", align: "right", badge: !0 },
				],
				s = k(() => A.data);
			function x(o) {
				if (o.type === "Expense") return ie(o.amount);
				const h = oe(o.from_date, o.to_date);
				return o.label ? `${o.label}, ${h}` : h;
			}
			const p = k(() => {
					var O;
					const o = G().hour();
					return `${
						o < 12 ? "Good morning" : o < 17 ? "Good afternoon" : "Good evening"
					}, ${((O = s.value) == null ? void 0 : O.greeting_name) || ""}`
						.trim()
						.replace(/,$/, "");
				}),
				v = k(() => {
					var o;
					return D((o = s.value) == null ? void 0 : o.today, "dddd, D MMMM YYYY");
				});
			function m(o) {
				return G(o).format("D MMM");
			}
			return (
				P(() => A.fetch()),
				(o, h) => {
					const O = fe("RouterLink");
					return (
						n(),
						w(
							ae,
							{ loading: f(A).loading && !f(A).data },
							{
								default: r(() => {
									var _;
									return [
										u(te, { title: p.value, subtitle: v.value }, null, 8, [
											"title",
											"subtitle",
										]),
										s.value
											? (n(),
											  d(
													b,
													{ key: 0 },
													[
														u(
															Ye,
															{
																checkin: s.value.checkin,
																week: s.value.week,
																onChanged:
																	h[0] ||
																	(h[0] = (e) => f(A).reload()),
															},
															null,
															8,
															["checkin", "week"],
														),
														s.value.onboarding
															? (n(),
															  w(
																	N,
																	{
																		key: 0,
																		title: "Onboarding",
																		padded: !1,
																	},
																	{
																		action: r(() => [
																			a("div", qe, [
																				a(
																					"span",
																					Be,
																					i(
																						s.value
																							.onboarding
																							.done,
																					) +
																						" of " +
																						i(
																							s.value
																								.onboarding
																								.total,
																						) +
																						" done ",
																					1,
																				),
																				u(
																					M,
																					{
																						status: s
																							.value
																							.onboarding
																							.status,
																					},
																					null,
																					8,
																					["status"],
																				),
																			]),
																		]),
																		default: r(() => [
																			u(
																				f(me),
																				{
																					class: "px-3.5 pb-2.5",
																					value: s.value
																						.onboarding
																						.pct,
																					size: "md",
																				},
																				null,
																				8,
																				["value"],
																			),
																			u(
																				z,
																				{
																					columns: L,
																					rows: s.value
																						.onboarding
																						.tasks,
																					"id-key":
																						"activity",
																				},
																				{
																					"cell-activity":
																						r(
																							({
																								row: e,
																							}) => [
																								a(
																									"span",
																									Ee,
																									i(
																										e.activity,
																									),
																									1,
																								),
																							],
																						),
																					"cell-owner":
																						r(
																							({
																								row: e,
																							}) => [
																								a(
																									"span",
																									{
																										class: j(
																											e.mine
																												? "text-ink-gray-8"
																												: "text-ink-gray-6",
																										),
																									},
																									i(
																										e.owner,
																									),
																									3,
																								),
																							],
																						),
																					"cell-due": r(
																						({
																							row: e,
																						}) => [
																							a(
																								"span",
																								He,
																								i(
																									e.due
																										? f(
																												D,
																										  )(
																												e.due,
																										  )
																										: "—",
																								),
																								1,
																							),
																						],
																					),
																					"cell-status":
																						r(
																							({
																								row: e,
																							}) => [
																								u(
																									M,
																									{
																										status: e.status,
																									},
																									null,
																									8,
																									[
																										"status",
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
															  ))
															: I("", !0),
														a("div", Ve, [
															(n(),
															d(
																b,
																null,
																C(c, (e) =>
																	u(
																		O,
																		{
																			key: e.label,
																			to: e.to,
																			class: "flex items-center gap-2.5 rounded-6 border border-outline-gray-1 bg-surface-base p-3 transition-colors hover:bg-surface-gray-1",
																		},
																		{
																			default: r(() => [
																				a("span", ze, [
																					a(
																						"span",
																						{
																							class: j(
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
																				a(
																					"span",
																					Ue,
																					i(e.label),
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
														(_ = s.value.pending_approvals) != null &&
														_.length
															? (n(),
															  w(
																	N,
																	{
																		key: 1,
																		title: "Waiting on You",
																	},
																	{
																		action: r(() => [
																			u(
																				M,
																				{
																					status: "pending",
																					label: String(
																						s.value
																							.pending_approvals
																							.length,
																					),
																				},
																				null,
																				8,
																				["label"],
																			),
																		]),
																		default: r(() => [
																			a("ul", We, [
																				(n(!0),
																				d(
																					b,
																					null,
																					C(
																						s.value
																							.pending_approvals,
																						(e) => (
																							n(),
																							d(
																								"li",
																								{
																									key: e.name,
																									class: "flex items-center justify-between gap-2",
																								},
																								[
																									u(
																										U,
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
																									h[1] ||
																										(h[1] =
																											a(
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
															: I("", !0),
														u(
															N,
															{ title: "My Requests", padded: !1 },
															{
																action: r(() => [
																	u(f(q), {
																		variant: "ghost",
																		route: "/leave",
																		label: "View All",
																	}),
																]),
																default: r(() => [
																	u(
																		z,
																		{
																			columns: T,
																			rows: s.value.requests,
																			"empty-message":
																				"You have not raised any requests yet.",
																		},
																		{
																			"cell-detail": r(
																				({ row: e }) => [
																					a(
																						"span",
																						Fe,
																						i(x(e)),
																						1,
																					),
																				],
																			),
																			"cell-submitted": r(
																				({ row: e }) => [
																					a(
																						"span",
																						Ge,
																						i(
																							f(D)(
																								e.submitted,
																							),
																						),
																						1,
																					),
																				],
																			),
																			"cell-approver": r(
																				({ row: e }) => [
																					a(
																						"span",
																						Ke,
																						i(
																							e.approver_name ||
																								"—",
																						),
																						1,
																					),
																				],
																			),
																			"cell-status": r(
																				({ row: e }) => [
																					u(
																						M,
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
														u(
															N,
															{ title: "Out Today" },
															{
																action: r(() => [
																	a(
																		"span",
																		Pe,
																		i(
																			s.value.out_today
																				.count,
																		) +
																			" of " +
																			i(
																				s.value.out_today
																					.total,
																			),
																		1,
																	),
																]),
																default: r(() => [
																	s.value.out_today.people.length
																		? (n(),
																		  d("ul", Je, [
																				(n(!0),
																				d(
																					b,
																					null,
																					C(
																						s.value
																							.out_today
																							.people,
																						(e) => (
																							n(),
																							d(
																								"li",
																								{
																									key: e.employee,
																									class: "flex items-center justify-between gap-2",
																								},
																								[
																									u(
																										U,
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
																									u(
																										M,
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
																		  w(W, {
																				key: 1,
																				message:
																					"Everybody is in today.",
																		  })),
																]),
																_: 1,
															},
														),
														u(
															N,
															{ title: "Coming Up" },
															{
																default: r(() => [
																	s.value.coming_up.length
																		? (n(),
																		  d("dl", Qe, [
																				(n(!0),
																				d(
																					b,
																					null,
																					C(
																						s.value
																							.coming_up,
																						(e) => (
																							n(),
																							w(
																								se,
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
																		  w(W, {
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
											: I("", !0),
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
export { ut as default };
