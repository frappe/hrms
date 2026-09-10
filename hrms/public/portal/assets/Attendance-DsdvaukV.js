var T = (y, c, s) =>
	new Promise((x, _) => {
		var g = (t) => {
				try {
					r(s.next(t));
				} catch (e) {
					_(e);
				}
			},
			b = (t) => {
				try {
					r(s.throw(t));
				} catch (e) {
					_(e);
				}
			},
			r = (t) => (t.done ? x(t.value) : Promise.resolve(t.value).then(g, b));
		r((s = s.apply(y, c)).next());
	});
import {
	o,
	h as i,
	e as l,
	F as p,
	i as k,
	t as v,
	s as E,
	a as A,
	L as W,
	f as n,
	w as d,
	g as m,
	I as B,
	N as H,
	O as L,
	k as F,
	d as V,
	z as O,
	B as D,
	P as j,
} from "./frappe-ui-D0k6koYp.js";
import { a as K, _ as C, b as R } from "./SectionCard-C5Qs8pBJ.js";
import { _ as z } from "./DashGrid-CGnJY6QD.js";
import { _ as U } from "./StatTiles-CcQndbp7.js";
import { _ as P } from "./StatusBadge-sSVuNJEI.js";
import { _ as w } from "./FieldRow-DoxIhPye.js";
import { _ as Y } from "./EmptyState-38_uLDf3.js";
import { c as G, f as h, t as I, d as q, s as J } from "./index-BSaIzYPn.js";
import { _ as Q } from "./RequestDialog-UMsP4D4j.js";
import "./RequestField-CEA0aLLd.js";
import "./DateField-DafgtgxX.js";
import "./toast-BPVivXt-.js";
const X = { class: "flex flex-col gap-3" },
	Z = { class: "hidden md:block" },
	ee = { class: "grid grid-cols-7 gap-1" },
	te = { class: "nums font-medium" },
	ae = { class: "mt-auto truncate opacity-90" },
	se = { class: "md:hidden" },
	le = { class: "flex min-w-0 items-center gap-2.5" },
	ne = { class: "nums w-10 shrink-0 text-base text-ink-gray-5" },
	re = { class: "truncate text-p-base text-ink-gray-8" },
	oe = { class: "nums shrink-0 text-base text-ink-gray-5" },
	ie = { class: "flex flex-wrap gap-x-3 gap-y-1.5" },
	ue = { class: "text-[10px] text-ink-gray-5" },
	de = {
		__name: "MonthCalendar",
		props: { days: { type: Array, default: () => [] } },
		setup(y) {
			const c = y,
				s = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
				x = [
					{ label: "Present", class: "bg-surface-green-2" },
					{ label: "Half day", class: "bg-surface-amber-2" },
					{ label: "Leave", class: "bg-surface-blue-2" },
					{ label: "Absent", class: "bg-surface-red-2" },
					{ label: "Holiday", class: "bg-surface-gray-4" },
				],
				_ = A(() => (c.days.length ? c.days[0].weekday : 0)),
				g = A(() => c.days.filter((e) => e.status || e.holiday || e.leave_type));
			function b(e) {
				if (e.weekly_off || (e.holiday && !e.status))
					return "bg-surface-gray-3 text-ink-gray-4";
				switch (e.status) {
					case "Present":
					case "Work From Home":
						return "bg-surface-green-2 text-ink-green-6";
					case "Half Day":
						return "bg-surface-amber-2 text-ink-amber-6";
					case "On Leave":
						return "bg-surface-blue-2 text-ink-blue-6";
					case "Absent":
						return "bg-surface-red-2 text-ink-red-8";
					default:
						return "bg-surface-gray-2 text-ink-gray-5";
				}
			}
			function r(e) {
				return e.hours
					? `${e.hours}h`
					: e.leave_type
					  ? e.leave_type
					  : e.holiday
					    ? e.weekly_off
								? ""
								: e.holiday
					    : "";
			}
			function t(e) {
				return G(e).format("D MMM");
			}
			return (e, u) => (
				o(),
				i("div", X, [
					l("div", Z, [
						l("div", ee, [
							(o(),
							i(
								p,
								null,
								k(s, (a) =>
									l(
										"div",
										{
											key: a,
											class: "pb-1 text-center text-base text-ink-gray-4",
										},
										v(a),
										1,
									),
								),
								64,
							)),
							(o(!0),
							i(
								p,
								null,
								k(_.value, (a) => (o(), i("div", { key: `b${a}` }))),
								128,
							)),
							(o(!0),
							i(
								p,
								null,
								k(
									y.days,
									(a) => (
										o(),
										i(
											"div",
											{
												key: a.date,
												class: E([
													"flex h-[52px] flex-col rounded-4 px-1.5 py-1 text-[10px]",
													[
														b(a),
														a.is_today &&
															"ring-1 ring-inset ring-outline-gray-4",
													],
												]),
											},
											[
												l("span", te, v(a.day), 1),
												l("span", ae, v(r(a)), 1),
											],
											2,
										)
									),
								),
								128,
							)),
						]),
					]),
					l("ul", se, [
						(o(!0),
						i(
							p,
							null,
							k(
								g.value,
								(a) => (
									o(),
									i(
										"li",
										{
											key: a.date,
											class: "flex items-center justify-between gap-3 border-b border-outline-gray-1 py-2 last:border-0",
										},
										[
											l("div", le, [
												l("span", ne, v(t(a.date)), 1),
												l(
													"span",
													re,
													v(
														a.holiday ||
															a.leave_type ||
															a.status ||
															"Not marked",
													),
													1,
												),
											]),
											l("span", oe, v(a.hours ? `${a.hours}h` : ""), 1),
										],
									)
								),
							),
							128,
						)),
					]),
					l("div", ie, [
						(o(),
						i(
							p,
							null,
							k(x, (a) =>
								l("span", { key: a.label, class: "flex items-center gap-1.5" }, [
									l(
										"span",
										{ class: E(["h-2.5 w-2.5 rounded-1", a.class]) },
										null,
										2,
									),
									l("span", ue, v(a.label), 1),
								]),
							),
							64,
						)),
					]),
				])
			);
		},
	},
	ce = { class: "nums text-base-semibold text-ink-gray-8", "aria-live": "polite" },
	fe = { class: "flex items-center gap-1" },
	me = { class: "flex flex-col" },
	ve = { key: 0 },
	_e = { class: "text-p-base text-ink-gray-8" },
	be = { key: 1, class: "px-3.5 pb-3.5" },
	pe = { class: "flex flex-col" },
	Se = {
		__name: "Attendance",
		setup(y) {
			const c = D(!1),
				s = A(() => h.data),
				x = A(() => {
					var t, e, u, a, f, $;
					const r = ((t = s.value) == null ? void 0 : t.stats) || {};
					return [
						{
							label: "Present",
							value: (e = r.present) != null ? e : 0,
							hint: `of ${(u = r.working_days) != null ? u : 0} working days`,
						},
						{
							label: "On Leave",
							value: (a = r.on_leave) != null ? a : 0,
							hint: r.absent ? `${r.absent} absent` : "",
						},
						{
							label: "Unmarked",
							value: (f = r.unmarked) != null ? f : 0,
							hint: r.unmarked ? "needs action" : "all accounted for",
						},
						{
							label: "Avg Hours",
							value: ($ = r.avg_hours) != null ? $ : 0,
							hint: "per marked day",
						},
					];
				}),
				_ = D(null),
				g = D(null);
			function b(r) {
				return T(this, null, function* () {
					var f, $, M;
					const t =
						r < 0
							? (f = s.value) == null
								? void 0
								: f.prev_month
							: ($ = s.value) == null
							  ? void 0
							  : $.next_month;
					if (!t) return;
					yield h.fetch({ month: t }), yield j();
					const e = (N) => {
							var S;
							return (S = N == null ? void 0 : N.$el) != null ? S : N;
						},
						u = e(r < 0 ? _.value : g.value),
						a = e(r < 0 ? g.value : _.value);
					(M = u != null && u.disabled ? a : u) == null || M.focus();
				});
			}
			return (
				W(() => h.fetch()),
				(r, t) => (
					o(),
					i(
						p,
						null,
						[
							n(
								R,
								{ loading: m(h).loading && !m(h).data },
								{
									default: d(() => [
										n(
											K,
											{
												title: "Attendance",
												subtitle: "Your month at a glance",
											},
											{
												actions: d(() => {
													var e, u, a;
													return [
														l(
															"div",
															{
																class: "flex items-center gap-2",
																role: "group",
																"aria-label": "Month",
																onKeydown: [
																	t[2] ||
																		(t[2] = H(
																			L(
																				(f) => b(-1),
																				["prevent"],
																			),
																			["left"],
																		)),
																	t[3] ||
																		(t[3] = H(
																			L(
																				(f) => b(1),
																				["prevent"],
																			),
																			["right"],
																		)),
																],
															},
															[
																l(
																	"span",
																	ce,
																	v(
																		((e = s.value) == null
																			? void 0
																			: e.month_label) ||
																			"—",
																	),
																	1,
																),
																l("div", fe, [
																	n(
																		m(B),
																		{
																			ref_key: "prevBtn",
																			ref: _,
																			variant: "subtle",
																			icon: "lucide-chevron-left",
																			label: "Previous month",
																			disabled: !(
																				(u = s.value) !=
																					null &&
																				u.prev_month
																			),
																			onClick:
																				t[0] ||
																				(t[0] = (f) =>
																					b(-1)),
																		},
																		null,
																		8,
																		["disabled"],
																	),
																	n(
																		m(B),
																		{
																			ref_key: "nextBtn",
																			ref: g,
																			variant: "subtle",
																			icon: "lucide-chevron-right",
																			label: "Next month",
																			disabled: !(
																				(a = s.value) !=
																					null &&
																				a.next_month
																			),
																			onClick:
																				t[1] ||
																				(t[1] = (f) =>
																					b(1)),
																		},
																		null,
																		8,
																		["disabled"],
																	),
																]),
															],
															32,
														),
														n(
															m(B),
															{
																variant: "solid",
																onClick:
																	t[4] ||
																	(t[4] = (f) => (c.value = !0)),
															},
															{
																default: d(() => [
																	...(t[8] ||
																		(t[8] = [
																			F("Regularise", -1),
																		])),
																]),
																_: 1,
															},
														),
													];
												}),
												_: 1,
											},
										),
										s.value
											? (o(),
											  i(
													p,
													{ key: 0 },
													[
														n(U, { tiles: x.value }, null, 8, [
															"tiles",
														]),
														n(z, null, {
															main: d(() => [
																n(
																	C,
																	{ title: s.value.month_label },
																	{
																		default: d(() => [
																			n(
																				de,
																				{
																					days: s.value
																						.days,
																				},
																				null,
																				8,
																				["days"],
																			),
																		]),
																		_: 1,
																	},
																	8,
																	["title"],
																),
															]),
															side: d(() => [
																n(
																	C,
																	{ title: "Today" },
																	{
																		action: d(() => [
																			n(
																				P,
																				{
																					status: s.value
																						.today
																						.checked_in
																						? "On shift"
																						: "Not checked in",
																					label: s.value
																						.today
																						.checked_in
																						? "On shift"
																						: "Not checked in",
																				},
																				null,
																				8,
																				[
																					"status",
																					"label",
																				],
																			),
																		]),
																		default: d(() => [
																			l("dl", me, [
																				n(
																					w,
																					{
																						label: "Checked in",
																						value: s
																							.value
																							.today
																							.since
																							? m(I)(
																									s
																										.value
																										.today
																										.since,
																							  )
																							: "",
																						nums: "",
																					},
																					null,
																					8,
																					["value"],
																				),
																				n(
																					w,
																					{
																						label: "Source",
																						value:
																							s.value
																								.today
																								.device ||
																							"Web",
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
																n(
																	C,
																	{
																		title: "Needs Action",
																		padded: !1,
																	},
																	{
																		action: d(() => [
																			s.value.stats.unmarked
																				? (o(),
																				  V(
																						P,
																						{
																							key: 0,
																							status: "unmarked",
																							label: String(
																								s
																									.value
																									.stats
																									.unmarked,
																							),
																						},
																						null,
																						8,
																						["label"],
																				  ))
																				: O("", !0),
																		]),
																		default: d(() => [
																			s.value.unmarked.length
																				? (o(),
																				  i("ul", ve, [
																						(o(!0),
																						i(
																							p,
																							null,
																							k(
																								s
																									.value
																									.unmarked,
																								(
																									e,
																								) => (
																									o(),
																									i(
																										"li",
																										{
																											key: e.date,
																											class: "flex items-center justify-between gap-3 border-b border-outline-gray-1 px-3.5 py-2.5 last:border-0",
																										},
																										[
																											l(
																												"div",
																												null,
																												[
																													l(
																														"div",
																														_e,
																														v(
																															m(
																																q,
																															)(
																																e.date,
																															),
																														),
																														1,
																													),
																													t[9] ||
																														(t[9] =
																															l(
																																"div",
																																{
																																	class: "text-base text-ink-gray-5",
																																},
																																" No attendance marked ",
																																-1,
																															)),
																												],
																											),
																											n(
																												m(
																													B,
																												),
																												{
																													class: "shrink-0",
																													variant:
																														"ghost",
																													label: "Regularise",
																													onClick:
																														t[5] ||
																														(t[5] =
																															(
																																u,
																															) =>
																																(c.value =
																																	!0)),
																												},
																											),
																										],
																									)
																								),
																							),
																							128,
																						)),
																				  ]))
																				: (o(),
																				  i("div", be, [
																						n(Y, {
																							message:
																								"Every past day this month is accounted for.",
																						}),
																				  ])),
																		]),
																		_: 1,
																	},
																),
																n(
																	C,
																	{
																		title: "Shift",
																		"readonly-label":
																			"HR-owned",
																	},
																	{
																		default: d(() => {
																			var e;
																			return [
																				l("dl", pe, [
																					n(
																						w,
																						{
																							label: "Assigned",
																							value:
																								(e =
																									s
																										.value
																										.shift) ==
																								null
																									? void 0
																									: e.name,
																							locked: "",
																						},
																						null,
																						8,
																						["value"],
																					),
																					n(
																						w,
																						{
																							label: "Timing",
																							value: m(
																								J,
																							)(
																								s
																									.value
																									.shift,
																							),
																							locked: "",
																							nums: "",
																						},
																						null,
																						8,
																						["value"],
																					),
																					n(
																						w,
																						{
																							label: "Weekly off",
																							value: s
																								.value
																								.weekly_off,
																							locked: "",
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
											: O("", !0),
									]),
									_: 1,
								},
								8,
								["loading"],
							),
							n(
								Q,
								{
									open: c.value,
									"onUpdate:open": t[6] || (t[6] = (e) => (c.value = e)),
									type: "attendance",
									onSaved: t[7] || (t[7] = (e) => m(h).fetch()),
								},
								null,
								8,
								["open"],
							),
						],
						64,
					)
				)
			);
		},
	};
export { Se as default };
