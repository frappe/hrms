var U = (y, I, c) =>
	new Promise((L, C) => {
		var M = (m) => {
				try {
					l(c.next(m));
				} catch (b) {
					C(b);
				}
			},
			_ = (m) => {
				try {
					l(c.throw(m));
				} catch (b) {
					C(b);
				}
			},
			l = (m) => (m.done ? L(m.value) : Promise.resolve(m.value).then(M, _));
		l((c = c.apply(y, I)).next());
	});
import {
	L as Q,
	M as ae,
	o,
	e as x,
	w as s,
	g as t,
	t as n,
	f as i,
	i as g,
	z as R,
	h as d,
	I as A,
	l as W,
	F as w,
	j as D,
	s as V,
	a as k,
	B as T,
	N as se,
	O as le,
	d as ne,
	b as ie,
} from "./frappe-ui-CXkWuvNK.js";
import { _ as $, a as oe, b as re } from "./SectionCard-BKeIA1B1.js";
import { _ as q } from "./DataTable-KquPBl5L.js";
import { _ as f } from "./StatusBadge-DcMGXIA6.js";
import { _ as F } from "./PersonRow-BtXbdUjH.js";
import { _ as ue } from "./FieldRow-2cmCHPuL.js";
import { _ as G } from "./EmptyState-DhAxAin0.js";
import {
	d as N,
	t as B,
	e as ce,
	m as de,
	s as K,
	h as j,
	a as P,
	b as ge,
	c as J,
} from "./index-BpEXs0_U.js";
import { n as me, a as pe, e as _e } from "./toast-Ca-cKV9o.js";
const ye = { class: "flex flex-wrap items-start justify-between gap-3" },
	he = { class: "min-w-0" },
	fe = { class: "text-base text-ink-gray-5" },
	ke = { class: "nums mt-0.5 text-4xl-semibold leading-tight text-ink-gray-9" },
	be = { class: "mt-1.5 flex flex-wrap items-center gap-2" },
	ve = { key: 0, class: "text-base text-ink-gray-5" },
	xe = { class: "flex shrink-0 gap-2" },
	$e = ["title", "tabindex", "aria-pressed", "aria-label", "onClick"],
	we = { class: "text-[10px] text-ink-gray-4" },
	Ce = { key: 0, class: "rounded-6 border border-outline-gray-1 bg-surface-gray-1 px-3 py-2.5" },
	Me = { class: "flex flex-wrap items-center justify-between gap-2" },
	Oe = { class: "flex min-w-0 flex-wrap items-center gap-2" },
	Re = { class: "text-base-semibold text-ink-gray-8" },
	De = { key: 0, class: "truncate text-base text-ink-gray-5" },
	Ne = { class: "mt-2 grid grid-cols-2 gap-x-4 gap-y-2 sm:grid-cols-4" },
	Ae = { class: "text-sm text-ink-gray-5" },
	Ie = ["title"],
	Le = { class: "mt-2.5 border-t border-outline-gray-1 pt-2.5" },
	Se = { key: 0, class: "mt-1.5 flex flex-wrap gap-1.5" },
	Te = { class: "text-sm text-ink-gray-6" },
	je = { class: "nums text-sm text-ink-gray-8" },
	Ve = { key: 1, class: "mt-1 text-base text-ink-gray-5" },
	Ye = {
		__name: "CheckInCard",
		props: {
			checkin: { type: Object, default: () => ({}) },
			week: { type: Array, default: () => [] },
		},
		emits: ["changed"],
		setup(y, { emit: I }) {
			const c = y,
				L = I,
				C = T("00:00:00"),
				M = T(!1),
				_ = T(null),
				l = T([]),
				m = T(null);
			let b = null;
			const Y = k(() => {
					const a = K(c.checkin.shift);
					return c.checkin.shift ? `${c.checkin.shift.name}, ${a}` : null;
				}),
				H = k(() =>
					c.checkin.checked_in
						? `Checked in at ${B(c.checkin.since)}`
						: "You have not checked in today",
				),
				u = k(() => c.week.find((a) => a.date === _.value) || null),
				v = k(() => {
					if (m.value !== null) return m.value;
					const a = c.week.findIndex((p) => p.is_today);
					return a === -1 ? 0 : a;
				});
			function h(a) {
				return a.status
					? a.status
					: a.weekly_off
					  ? "Weekly off"
					  : a.holiday
					    ? "Holiday"
					    : a.is_future
					      ? "Upcoming"
					      : "Not marked";
			}
			const S = k(() => {
					var a, p;
					return (
						((a = u.value) == null ? void 0 : a.leave_type) ||
						((p = u.value) == null ? void 0 : p.holiday) ||
						""
					);
				}),
				e = k(() => {
					const a = u.value;
					return a
						? [
								{ label: "In", value: B(a.in_time) },
								{ label: "Out", value: B(a.out_time) },
								{ label: "Hours", value: a.hours ? `${a.hours} h` : "—" },
								{
									label: "Shift",
									value: a.shift ? `${a.shift.name}, ${K(a.shift)}` : "—",
								},
						  ]
						: [];
				});
			function X(a) {
				_.value = _.value === a.date ? null : a.date;
			}
			function Z(a) {
				const p = { ArrowLeft: -1, ArrowRight: 1 }[a.key];
				let O;
				if (p) O = v.value + p;
				else if (a.key === "Home") O = 0;
				else if (a.key === "End") O = c.week.length - 1;
				else return;
				a.preventDefault(),
					(m.value = Math.max(0, Math.min(c.week.length - 1, O))),
					se(() => {
						var r;
						return (r = l.value[m.value]) == null ? void 0 : r.focus();
					});
			}
			function E() {
				C.value = c.checkin.checked_in ? ce(c.checkin.since) : "00:00:00";
			}
			function ee() {
				return U(this, null, function* () {
					M.value = !0;
					try {
						yield de.submit({ log_type: c.checkin.checked_in ? "OUT" : "IN" }),
							me(c.checkin.checked_in ? "Checked out" : "Checked in"),
							L("changed");
					} catch (a) {
						pe("Could not record that", _e(a, "Try again in a moment."));
					} finally {
						M.value = !1;
					}
				});
			}
			function te(a) {
				switch (a.status) {
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
				Q(() => {
					E(), (b = setInterval(E, 1e3));
				}),
				ae(() => clearInterval(b)),
				(a, p) => (
					o(),
					x($, null, {
						default: s(() => {
							var O;
							return [
								t("div", ye, [
									t("div", he, [
										t("p", fe, n(H.value), 1),
										t("p", ke, n(y.checkin.checked_in ? C.value : "—"), 1),
										t("div", be, [
											i(
												f,
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
											Y.value
												? (o(), g("span", ve, n(Y.value), 1))
												: R("", !0),
										]),
									]),
									t("div", xe, [
										i(
											d(A),
											{
												variant: "subtle",
												onClick:
													p[0] ||
													(p[0] = (r) => a.$router.push("/attendance")),
											},
											{
												default: s(() => [
													...(p[2] || (p[2] = [W("View Log", -1)])),
												]),
												_: 1,
											},
										),
										i(
											d(A),
											{ variant: "solid", loading: M.value, onClick: ee },
											{
												default: s(() => [
													W(
														n(
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
								t(
									"div",
									{
										class: "grid grid-cols-7 gap-1.5",
										role: "toolbar",
										"aria-label": "This week",
										onKeydown: Z,
									},
									[
										(o(!0),
										g(
											w,
											null,
											D(
												y.week,
												(r, z) => (
													o(),
													g(
														"button",
														{
															key: r.date,
															ref_for: !0,
															ref_key: "pills",
															ref: l,
															type: "button",
															title: `${d(N)(
																r.date,
																"dddd D MMMM",
															)}, ${h(r)}`,
															class: "flex cursor-pointer flex-col items-center gap-1 rounded-4 p-1 transition-colors hover:bg-surface-gray-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3",
															tabindex: z === v.value ? 0 : -1,
															"aria-pressed": _.value === r.date,
															"aria-label": `${d(N)(
																r.date,
																"dddd D MMMM",
															)}, ${h(r)}`,
															onClick: (it) => X(r),
														},
														[
															t("span", we, n(r.label), 1),
															t(
																"span",
																{
																	class: V([
																		"h-6 w-full rounded-4",
																		[
																			te(r),
																			r.is_today &&
																				"ring-1 ring-inset ring-outline-gray-4",
																		],
																	]),
																},
																null,
																2,
															),
															t(
																"span",
																{
																	class: V([
																		"-mb-1 h-px w-full transition-colors",
																		_.value === r.date
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
														$e,
													)
												),
											),
											128,
										)),
									],
									32,
								),
								u.value
									? (o(),
									  g("div", Ce, [
											t("div", Me, [
												t("div", Oe, [
													t(
														"span",
														Re,
														n(d(N)(u.value.date, "dddd, D MMMM")),
														1,
													),
													i(
														f,
														{ status: h(u.value), label: h(u.value) },
														null,
														8,
														["status", "label"],
													),
													S.value
														? (o(), g("span", De, n(S.value), 1))
														: R("", !0),
												]),
												i(d(A), {
													variant: "ghost",
													icon: "lucide-x",
													label: "Close day",
													onClick:
														p[1] || (p[1] = (r) => (_.value = null)),
												}),
											]),
											t("dl", Ne, [
												(o(!0),
												g(
													w,
													null,
													D(
														e.value,
														(r) => (
															o(),
															g("div", { key: r.label }, [
																t("dt", Ae, n(r.label), 1),
																t(
																	"dd",
																	{
																		class: "nums truncate text-base text-ink-gray-8",
																		title: r.value,
																	},
																	n(r.value),
																	9,
																	Ie,
																),
															])
														),
													),
													128,
												)),
											]),
											t("div", Le, [
												p[3] ||
													(p[3] = t(
														"p",
														{ class: "text-sm text-ink-gray-5" },
														"Check-ins",
														-1,
													)),
												(O = u.value.logs) != null && O.length
													? (o(),
													  g("ul", Se, [
															(o(!0),
															g(
																w,
																null,
																D(
																	u.value.logs,
																	(r, z) => (
																		o(),
																		g(
																			"li",
																			{
																				key: z,
																				class: "flex items-center gap-1.5 rounded-full border border-outline-gray-1 bg-surface-base py-0.5 pl-1.5 pr-2.5",
																			},
																			[
																				t(
																					"span",
																					{
																						class: V([
																							"h-1.5 w-1.5 rounded-full",
																							r.log_type ===
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
																				t(
																					"span",
																					Te,
																					n(r.log_type),
																					1,
																				),
																				t(
																					"span",
																					je,
																					n(
																						d(B)(
																							r.time,
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
													: (o(),
													  g(
															"p",
															Ve,
															n(
																u.value.is_future
																	? "Nothing recorded yet."
																	: "No check-ins on this day.",
															),
															1,
													  )),
											]),
									  ]))
									: R("", !0),
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
	He = { class: "text-ink-gray-8" },
	ze = { class: "nums text-ink-gray-5" },
	Ee = { class: "grid grid-cols-2 gap-3 sm:grid-cols-3" },
	Ue = {
		class: "flex h-7 w-7 shrink-0 items-center justify-center rounded-4 bg-surface-gray-3 text-ink-gray-7",
	},
	We = { class: "text-base leading-tight text-ink-gray-8" },
	Fe = { class: "flex flex-col gap-2.5" },
	Ge = { class: "text-ink-gray-8" },
	Ke = { class: "nums text-ink-gray-6" },
	Pe = { class: "nums text-ink-gray-6" },
	Je = { class: "text-ink-gray-6" },
	Qe = { class: "text-ink-gray-8" },
	Xe = { class: "nums text-ink-gray-5" },
	Ze = { class: "text-ink-gray-6" },
	et = { class: "text-ink-gray-8" },
	tt = { class: "nums text-ink-gray-6" },
	at = { class: "nums text-ink-gray-5" },
	st = { class: "text-base text-ink-gray-5" },
	lt = { key: 0, class: "flex flex-col gap-2" },
	nt = { key: 0, class: "flex flex-col" },
	ht = {
		__name: "Home",
		setup(y) {
			const I = [
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
				L = [
					{ key: "label", label: "Type", primary: !0 },
					{ key: "dates", label: "Dates", nums: !0 },
					{ key: "days", label: "Days", align: "right", nums: !0, hideOnMobile: !0 },
					{ key: "approver", label: "Approver", hideOnMobile: !0 },
					{ key: "status", label: "Status", align: "right", badge: !0 },
				],
				C = [
					{ key: "amount", label: "Amount", primary: !0, nums: !0 },
					{ key: "submitted", label: "Submitted", nums: !0, muted: !0 },
					{ key: "approver", label: "Approver", hideOnMobile: !0 },
					{ key: "status", label: "Status", align: "right", badge: !0 },
				],
				M = [
					{ key: "label", label: "Reason", primary: !0 },
					{ key: "dates", label: "Dates", nums: !0 },
					{ key: "submitted", label: "Raised", nums: !0, muted: !0, hideOnMobile: !0 },
					{ key: "status", label: "Status", align: "right", badge: !0 },
				],
				_ = ie(),
				l = k(() => j.data);
			function m(u) {
				_.push(`/requests/${u.type.toLowerCase()}/${encodeURIComponent(u.name)}`);
			}
			const b = k(() => {
					var h;
					const u = J().hour();
					return `${
						u < 12 ? "Good morning" : u < 17 ? "Good afternoon" : "Good evening"
					}, ${((h = l.value) == null ? void 0 : h.greeting_name) || ""}`
						.trim()
						.replace(/,$/, "");
				}),
				Y = k(() => {
					var u;
					return N((u = l.value) == null ? void 0 : u.today, "dddd, D MMMM YYYY");
				});
			function H(u) {
				return J(u).format("D MMM");
			}
			return (
				Q(() => j.fetch()),
				(u, v) => {
					const h = ne("RouterLink");
					return (
						o(),
						x(
							re,
							{ loading: d(j).loading && !d(j).data },
							{
								default: s(() => {
									var S;
									return [
										i(oe, { title: b.value, subtitle: Y.value }, null, 8, [
											"title",
											"subtitle",
										]),
										l.value
											? (o(),
											  g(
													w,
													{ key: 0 },
													[
														i(
															Ye,
															{
																checkin: l.value.checkin,
																week: l.value.week,
																onChanged:
																	v[0] ||
																	(v[0] = (e) => d(j).reload()),
															},
															null,
															8,
															["checkin", "week"],
														),
														l.value.onboarding
															? (o(),
															  x(
																	$,
																	{
																		key: 0,
																		title: "Onboarding",
																		padded: !1,
																	},
																	{
																		action: s(() => [
																			t("div", qe, [
																				t(
																					"span",
																					Be,
																					n(
																						l.value
																							.onboarding
																							.done,
																					) +
																						" of " +
																						n(
																							l.value
																								.onboarding
																								.total,
																						) +
																						" done ",
																					1,
																				),
																				i(
																					f,
																					{
																						status: l
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
																		default: s(() => [
																			i(
																				d(le),
																				{
																					class: "px-3.5 pb-2.5",
																					value: l.value
																						.onboarding
																						.pct,
																					size: "md",
																				},
																				null,
																				8,
																				["value"],
																			),
																			i(
																				q,
																				{
																					columns: I,
																					rows: l.value
																						.onboarding
																						.tasks,
																					"id-key":
																						"activity",
																				},
																				{
																					"cell-activity":
																						s(
																							({
																								row: e,
																							}) => [
																								t(
																									"span",
																									He,
																									n(
																										e.activity,
																									),
																									1,
																								),
																							],
																						),
																					"cell-owner":
																						s(
																							({
																								row: e,
																							}) => [
																								t(
																									"span",
																									{
																										class: V(
																											e.mine
																												? "text-ink-gray-8"
																												: "text-ink-gray-6",
																										),
																									},
																									n(
																										e.owner,
																									),
																									3,
																								),
																							],
																						),
																					"cell-due": s(
																						({
																							row: e,
																						}) => [
																							t(
																								"span",
																								ze,
																								n(
																									e.due
																										? d(
																												N,
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
																						s(
																							({
																								row: e,
																							}) => [
																								i(
																									f,
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
															: R("", !0),
														t("div", Ee, [
															(o(),
															g(
																w,
																null,
																D(c, (e) =>
																	i(
																		h,
																		{
																			key: e.label,
																			to: e.to,
																			class: "flex items-center gap-2.5 rounded-6 border border-outline-gray-1 bg-surface-base p-3 transition-colors hover:bg-surface-gray-1",
																		},
																		{
																			default: s(() => [
																				t("span", Ue, [
																					t(
																						"span",
																						{
																							class: V(
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
																				t(
																					"span",
																					We,
																					n(e.label),
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
														(S = l.value.pending_approvals) != null &&
														S.length
															? (o(),
															  x(
																	$,
																	{
																		key: 1,
																		title: "Waiting on You",
																	},
																	{
																		action: s(() => [
																			i(
																				f,
																				{
																					status: "pending",
																					label: String(
																						l.value
																							.pending_approvals
																							.length,
																					),
																				},
																				null,
																				8,
																				["label"],
																			),
																		]),
																		default: s(() => [
																			t("ul", Fe, [
																				(o(!0),
																				g(
																					w,
																					null,
																					D(
																						l.value
																							.pending_approvals,
																						(e) => (
																							o(),
																							g(
																								"li",
																								{
																									key: e.name,
																									class: "flex items-center justify-between gap-2",
																								},
																								[
																									i(
																										F,
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
																									v[1] ||
																										(v[1] =
																											t(
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
															: R("", !0),
														i(
															$,
															{ title: "My Leave", padded: !1 },
															{
																action: s(() => [
																	i(d(A), {
																		variant: "ghost",
																		route: "/leave",
																		label: "View All",
																	}),
																]),
																default: s(() => [
																	i(
																		q,
																		{
																			columns: L,
																			rows: l.value.requests
																				.leave,
																			clickable: "",
																			"empty-message":
																				"You have not applied for leave yet.",
																			onRowClick: m,
																		},
																		{
																			"cell-label": s(
																				({ row: e }) => [
																					t(
																						"span",
																						Ge,
																						n(e.label),
																						1,
																					),
																				],
																			),
																			"cell-dates": s(
																				({ row: e }) => [
																					t(
																						"span",
																						Ke,
																						n(
																							d(P)(
																								e.from_date,
																								e.to_date,
																							),
																						),
																						1,
																					),
																				],
																			),
																			"cell-days": s(
																				({ row: e }) => [
																					t(
																						"span",
																						Pe,
																						n(e.days),
																						1,
																					),
																				],
																			),
																			"cell-approver": s(
																				({ row: e }) => [
																					t(
																						"span",
																						Je,
																						n(
																							e.approver_name ||
																								"—",
																						),
																						1,
																					),
																				],
																			),
																			"cell-status": s(
																				({ row: e }) => [
																					i(
																						f,
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
														i(
															$,
															{ title: "My Claims", padded: !1 },
															{
																action: s(() => [
																	i(d(A), {
																		variant: "ghost",
																		route: "/expenses",
																		label: "View All",
																	}),
																]),
																default: s(() => [
																	i(
																		q,
																		{
																			columns: C,
																			rows: l.value.requests
																				.expense,
																			clickable: "",
																			"empty-message":
																				"You have not claimed any expenses yet.",
																			onRowClick: m,
																		},
																		{
																			"cell-amount": s(
																				({ row: e }) => [
																					t(
																						"span",
																						Qe,
																						n(
																							d(ge)(
																								e.amount,
																							),
																						),
																						1,
																					),
																				],
																			),
																			"cell-submitted": s(
																				({ row: e }) => [
																					t(
																						"span",
																						Xe,
																						n(
																							d(N)(
																								e.submitted,
																							),
																						),
																						1,
																					),
																				],
																			),
																			"cell-approver": s(
																				({ row: e }) => [
																					t(
																						"span",
																						Ze,
																						n(
																							e.approver_name ||
																								"—",
																						),
																						1,
																					),
																				],
																			),
																			"cell-status": s(
																				({ row: e }) => [
																					i(
																						f,
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
														l.value.requests.attendance.length
															? (o(),
															  x(
																	$,
																	{
																		key: 2,
																		title: "Regularisation",
																		padded: !1,
																	},
																	{
																		action: s(() => [
																			i(d(A), {
																				variant: "ghost",
																				route: "/attendance",
																				label: "View All",
																			}),
																		]),
																		default: s(() => [
																			i(
																				q,
																				{
																					columns: M,
																					rows: l.value
																						.requests
																						.attendance,
																					clickable: "",
																					onRowClick: m,
																				},
																				{
																					"cell-label":
																						s(
																							({
																								row: e,
																							}) => [
																								t(
																									"span",
																									et,
																									n(
																										e.label,
																									),
																									1,
																								),
																							],
																						),
																					"cell-dates":
																						s(
																							({
																								row: e,
																							}) => [
																								t(
																									"span",
																									tt,
																									n(
																										d(
																											P,
																										)(
																											e.from_date,
																											e.to_date,
																										),
																									),
																									1,
																								),
																							],
																						),
																					"cell-submitted":
																						s(
																							({
																								row: e,
																							}) => [
																								t(
																									"span",
																									at,
																									n(
																										d(
																											N,
																										)(
																											e.submitted,
																										),
																									),
																									1,
																								),
																							],
																						),
																					"cell-status":
																						s(
																							({
																								row: e,
																							}) => [
																								i(
																									f,
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
															: R("", !0),
														i(
															$,
															{ title: "Out Today" },
															{
																action: s(() => [
																	t(
																		"span",
																		st,
																		n(
																			l.value.out_today
																				.count,
																		) +
																			" of " +
																			n(
																				l.value.out_today
																					.total,
																			),
																		1,
																	),
																]),
																default: s(() => [
																	l.value.out_today.people.length
																		? (o(),
																		  g("ul", lt, [
																				(o(!0),
																				g(
																					w,
																					null,
																					D(
																						l.value
																							.out_today
																							.people,
																						(e) => (
																							o(),
																							g(
																								"li",
																								{
																									key: e.employee,
																									class: "flex items-center justify-between gap-2",
																								},
																								[
																									i(
																										F,
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
																									i(
																										f,
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
																		: (o(),
																		  x(G, {
																				key: 1,
																				message:
																					"Everybody is in today.",
																		  })),
																]),
																_: 1,
															},
														),
														i(
															$,
															{ title: "Coming Up" },
															{
																default: s(() => [
																	l.value.coming_up.length
																		? (o(),
																		  g("dl", nt, [
																				(o(!0),
																				g(
																					w,
																					null,
																					D(
																						l.value
																							.coming_up,
																						(e) => (
																							o(),
																							x(
																								ue,
																								{
																									key:
																										e.date +
																										e.label,
																									label: H(
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
																		: (o(),
																		  x(G, {
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
											: R("", !0),
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
export { ht as default };
