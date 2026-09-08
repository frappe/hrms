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
	s as i,
	k as n,
	F as p,
	t as k,
	x as v,
	v as E,
	a as A,
	P as F,
	h as l,
	g as d,
	R as H,
	S as L,
	i as m,
	M as C,
	B as O,
	f as R,
	C as P,
	U as V,
	e as M,
} from "./frappe-ui-BQ9PgXrr.js";
import { _ as B, a as j } from "./SectionCard-u_7VCKnT.js";
import { _ as K } from "./PageHead-3jtDpZ9g.js";
import { _ as U } from "./DashGrid-Bd23iLvt.js";
import { _ as Y } from "./StatTiles-YoNxs_Qn.js";
import { _ as W } from "./StatusBadge-Bqz4zlkD.js";
import { _ as w } from "./FieldRow-DbBPtAxY.js";
import { _ as z } from "./EmptyState-DNwecFw5.js";
import { a as G, f as h, t as q, d as I, s as J } from "./index-DKSqIuAQ.js";
import { _ as Q } from "./RequestDialog-TPB8mqrQ.js";
import "./toast-9qekBDJT.js";
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
						return "bg-surface-green-2 text-ink-green-3";
					case "Half Day":
						return "bg-surface-amber-2 text-ink-amber-3";
					case "On Leave":
						return "bg-surface-blue-2 text-ink-blue-3";
					case "Absent":
						return "bg-surface-red-2 text-ink-red-4";
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
					n("div", Z, [
						n("div", ee, [
							(o(),
							i(
								p,
								null,
								k(s, (a) =>
									n(
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
													"flex h-[52px] flex-col rounded px-1.5 py-1 text-[10px]",
													[
														b(a),
														a.is_today &&
															"ring-1 ring-inset ring-outline-gray-4",
													],
												]),
											},
											[
												n("span", te, v(a.day), 1),
												n("span", ae, v(r(a)), 1),
											],
											2,
										)
									),
								),
								128,
							)),
						]),
					]),
					n("ul", se, [
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
											n("div", le, [
												n("span", ne, v(t(a.date)), 1),
												n(
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
											n("span", oe, v(a.hours ? `${a.hours}h` : ""), 1),
										],
									)
								),
							),
							128,
						)),
					]),
					n("div", ie, [
						(o(),
						i(
							p,
							null,
							k(x, (a) =>
								n("span", { key: a.label, class: "flex items-center gap-1.5" }, [
									n(
										"span",
										{ class: E(["h-2.5 w-2.5 rounded-sm", a.class]) },
										null,
										2,
									),
									n("span", ue, v(a.label), 1),
								]),
							),
							64,
						)),
					]),
				])
			);
		},
	},
	ce = {
		class: "nums min-w-[7.5rem] text-center text-base font-semibold text-ink-gray-8",
		"aria-live": "polite",
	},
	fe = { class: "flex flex-col" },
	me = { key: 0 },
	ve = { class: "text-p-base text-ink-gray-8" },
	_e = { key: 1, class: "px-3.5 pb-3.5" },
	be = { class: "flex flex-col" },
	Me = {
		__name: "Attendance",
		setup(y) {
			const c = M(!1),
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
				_ = M(null),
				g = M(null);
			function b(r) {
				return T(this, null, function* () {
					var f, $, S;
					const t =
						r < 0
							? (f = s.value) == null
								? void 0
								: f.prev_month
							: ($ = s.value) == null
							  ? void 0
							  : $.next_month;
					if (!t) return;
					yield h.fetch({ month: t }), yield V();
					const e = (N) => {
							var D;
							return (D = N == null ? void 0 : N.$el) != null ? D : N;
						},
						u = e(r < 0 ? _.value : g.value),
						a = e(r < 0 ? g.value : _.value);
					(S = u != null && u.disabled ? a : u) == null || S.focus();
				});
			}
			return (
				F(() => h.fetch()),
				(r, t) => (
					o(),
					i(
						p,
						null,
						[
							l(
								j,
								{ loading: m(h).loading && !m(h).data },
								{
									default: d(() => [
										l(
											K,
											{
												title: "Attendance",
												subtitle: "Your month at a glance",
											},
											{
												actions: d(() => {
													var e, u, a;
													return [
														n(
															"div",
															{
																class: "flex items-center gap-1",
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
																	m(C),
																	{
																		ref_key: "prevBtn",
																		ref: _,
																		variant: "subtle",
																		icon: "chevron-left",
																		label: "Previous month",
																		disabled: !(
																			(e = s.value) !=
																				null &&
																			e.prev_month
																		),
																		onClick:
																			t[0] ||
																			(t[0] = (f) => b(-1)),
																	},
																	null,
																	8,
																	["disabled"],
																),
																n(
																	"span",
																	ce,
																	v(
																		((u = s.value) == null
																			? void 0
																			: u.month_label) ||
																			"—",
																	),
																	1,
																),
																l(
																	m(C),
																	{
																		ref_key: "nextBtn",
																		ref: g,
																		variant: "subtle",
																		icon: "chevron-right",
																		label: "Next month",
																		disabled: !(
																			(a = s.value) !=
																				null &&
																			a.next_month
																		),
																		onClick:
																			t[1] ||
																			(t[1] = (f) => b(1)),
																	},
																	null,
																	8,
																	["disabled"],
																),
															],
															32,
														),
														l(
															m(C),
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
																			O("Regularise", -1),
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
														l(Y, { tiles: x.value }, null, 8, [
															"tiles",
														]),
														l(U, null, {
															main: d(() => [
																l(
																	B,
																	{ title: s.value.month_label },
																	{
																		default: d(() => [
																			l(
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
																l(
																	B,
																	{ title: "Today" },
																	{
																		action: d(() => [
																			l(
																				W,
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
																			n("dl", fe, [
																				l(
																					w,
																					{
																						label: "Checked in",
																						value: s
																							.value
																							.today
																							.since
																							? m(q)(
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
																				l(
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
																l(
																	B,
																	{
																		title: "Needs Action",
																		padded: !1,
																	},
																	{
																		action: d(() => [
																			s.value.stats.unmarked
																				? (o(),
																				  R(
																						W,
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
																				: P("", !0),
																		]),
																		default: d(() => [
																			s.value.unmarked.length
																				? (o(),
																				  i("ul", me, [
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
																											n(
																												"div",
																												null,
																												[
																													n(
																														"div",
																														ve,
																														v(
																															m(
																																I,
																															)(
																																e.date,
																															),
																														),
																														1,
																													),
																													t[9] ||
																														(t[9] =
																															n(
																																"div",
																																{
																																	class: "text-base text-ink-gray-5",
																																},
																																"No attendance marked",
																																-1,
																															)),
																												],
																											),
																											l(
																												m(
																													C,
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
																				  i("div", _e, [
																						l(z, {
																							message:
																								"Every past day this month is accounted for.",
																						}),
																				  ])),
																		]),
																		_: 1,
																	},
																),
																l(
																	B,
																	{
																		title: "Shift",
																		"readonly-label":
																			"HR-owned",
																	},
																	{
																		default: d(() => {
																			var e;
																			return [
																				n("dl", be, [
																					l(
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
																					l(
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
																					l(
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
											: P("", !0),
									]),
									_: 1,
								},
								8,
								["loading"],
							),
							l(
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
export { Me as default };
