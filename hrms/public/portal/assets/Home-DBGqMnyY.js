var B = (m, x, c) =>
	new Promise((a, f) => {
		var h = (e) => {
				try {
					g(c.next(e));
				} catch (r) {
					f(r);
				}
			},
			k = (e) => {
				try {
					g(c.throw(e));
				} catch (r) {
					f(r);
				}
			},
			g = (e) => (e.done ? a(e.value) : Promise.resolve(e.value).then(h, k));
		g((c = c.apply(m, x)).next());
	});
import { _ as b, a as V } from "./SectionCard-u_7VCKnT.js";
import { _ as E } from "./PageHead-3jtDpZ9g.js";
import { _ as z } from "./DashGrid-Bd23iLvt.js";
import { _ as F } from "./DataTable-vZ6Z-J3d.js";
import { _ as O } from "./StatusBadge-Bqz4zlkD.js";
import { _ as D } from "./PersonRow-DZ4YBxpS.js";
import { _ as G } from "./BalanceBars-CBgUe-mJ.js";
import { _ as H } from "./FieldRow-DbBPtAxY.js";
import { _ as T } from "./EmptyState-DNwecFw5.js";
import {
	e as P,
	m as U,
	s as W,
	t as Q,
	h as $,
	d as Y,
	a as j,
	b as J,
	c as K,
} from "./index-DKSqIuAQ.js";
import { n as X, a as Z, e as ee } from "./toast-9qekBDJT.js";
import {
	P as S,
	Q as te,
	o as i,
	f as p,
	g as n,
	k as o,
	x as d,
	h as s,
	s as u,
	C as A,
	i as _,
	M as L,
	B as q,
	F as C,
	t as w,
	v as ae,
	a as M,
	e as I,
	q as se,
	p as R,
} from "./frappe-ui-BQ9PgXrr.js";
const ne = { class: "flex flex-wrap items-start justify-between gap-3" },
	le = { class: "min-w-0" },
	ie = { class: "text-base text-ink-gray-5" },
	oe = { class: "nums mt-0.5 text-3xl font-semibold leading-tight text-ink-gray-9" },
	ce = { class: "mt-1.5 flex flex-wrap items-center gap-2" },
	re = { key: 0, class: "text-base text-ink-gray-5" },
	ue = { class: "flex shrink-0 gap-2" },
	de = { class: "grid grid-cols-7 gap-1.5" },
	me = { class: "text-[10px] text-ink-gray-4" },
	_e = ["title"],
	ge = {
		__name: "CheckInCard",
		props: {
			checkin: { type: Object, default: () => ({}) },
			week: { type: Array, default: () => [] },
		},
		emits: ["changed"],
		setup(m, { emit: x }) {
			const c = m,
				a = x,
				f = I("00:00:00"),
				h = I(!1);
			let k = null;
			const g = M(() => {
					const t = W(c.checkin.shift);
					return c.checkin.shift ? `${c.checkin.shift.name}, ${t}` : null;
				}),
				e = M(() =>
					c.checkin.checked_in
						? `Checked in at ${Q(c.checkin.since)}`
						: "You have not checked in today",
				);
			function r() {
				f.value = c.checkin.checked_in ? P(c.checkin.since) : "00:00:00";
			}
			function y() {
				return B(this, null, function* () {
					h.value = !0;
					try {
						yield U.submit({ log_type: c.checkin.checked_in ? "OUT" : "IN" }),
							X(c.checkin.checked_in ? "Checked out" : "Checked in"),
							a("changed");
					} catch (t) {
						Z("Could not record that", ee(t, "Try again in a moment."));
					} finally {
						h.value = !1;
					}
				});
			}
			function l(t) {
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
				S(() => {
					r(), (k = setInterval(r, 1e3));
				}),
				te(() => clearInterval(k)),
				(t, N) => (
					i(),
					p(b, null, {
						default: n(() => [
							o("div", ne, [
								o("div", le, [
									o("p", ie, d(e.value), 1),
									o("p", oe, d(m.checkin.checked_in ? f.value : "—"), 1),
									o("div", ce, [
										s(
											O,
											{
												status: m.checkin.checked_in
													? "On shift"
													: "Not checked in",
												label: m.checkin.checked_in
													? "On shift"
													: "Not checked in",
											},
											null,
											8,
											["status", "label"],
										),
										g.value ? (i(), u("span", re, d(g.value), 1)) : A("", !0),
									]),
								]),
								o("div", ue, [
									s(
										_(L),
										{
											variant: "subtle",
											onClick:
												N[0] ||
												(N[0] = (v) => t.$router.push("/attendance")),
										},
										{
											default: n(() => [
												...(N[1] || (N[1] = [q("View Log", -1)])),
											]),
											_: 1,
										},
									),
									s(
										_(L),
										{ variant: "solid", loading: h.value, onClick: y },
										{
											default: n(() => [
												q(
													d(
														m.checkin.checked_in
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
							o("div", de, [
								(i(!0),
								u(
									C,
									null,
									w(
										m.week,
										(v) => (
											i(),
											u(
												"div",
												{
													key: v.date,
													class: "flex flex-col items-center gap-1",
												},
												[
													o("span", me, d(v.label), 1),
													o(
														"span",
														{
															class: ae([
																"h-6 w-full rounded",
																[
																	l(v),
																	v.is_today &&
																		"ring-1 ring-inset ring-outline-gray-4",
																],
															]),
															title: v.status || "Not marked",
														},
														null,
														10,
														_e,
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
	fe = { class: "grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5" },
	he = {
		class: "flex h-7 w-7 shrink-0 items-center justify-center rounded bg-surface-gray-3 text-ink-gray-7",
	},
	pe = { class: "text-base leading-tight text-ink-gray-8" },
	ke = { class: "text-ink-gray-8" },
	ye = { class: "nums text-ink-gray-5" },
	ve = { class: "text-ink-gray-6" },
	be = { class: "flex flex-col gap-2.5" },
	xe = { class: "text-base text-ink-gray-5" },
	$e = { key: 0, class: "flex flex-col gap-2" },
	Ce = { key: 0, class: "flex flex-col" },
	Re = {
		__name: "Home",
		setup(m) {
			const x = [
					{ label: "Apply Leave", to: "/leave", icon: "sunrise" },
					{ label: "Claim Expense", to: "/expenses", icon: "credit-card" },
					{ label: "Latest Payslip", to: "/payslips", icon: "file-text" },
					{ label: "Request Advance", to: "/advances", icon: "trending-up" },
					{ label: "Regularise", to: "/attendance", icon: "clock" },
				],
				c = [
					{ key: "type", label: "Type", hideOnMobile: !0 },
					{ key: "detail", label: "Detail", primary: !0 },
					{ key: "submitted", label: "Submitted", nums: !0, muted: !0 },
					{ key: "approver", label: "Approver" },
					{ key: "status", label: "Status", align: "right", badge: !0 },
				],
				a = M(() => $.data);
			function f(e) {
				if (e.type === "Expense") return J(e.amount);
				const r = K(e.from_date, e.to_date);
				return e.label ? `${e.label}, ${r}` : r;
			}
			const h = M(() => {
					var y;
					const e = j().hour();
					return `${
						e < 12 ? "Good morning" : e < 17 ? "Good afternoon" : "Good evening"
					}, ${((y = a.value) == null ? void 0 : y.greeting_name) || ""}`
						.trim()
						.replace(/,$/, "");
				}),
				k = M(() => {
					var e;
					return Y((e = a.value) == null ? void 0 : e.today, "dddd, D MMMM YYYY");
				});
			function g(e) {
				return j(e).format("D MMM");
			}
			return (
				S(() => $.fetch()),
				(e, r) => {
					const y = se("RouterLink");
					return (
						i(),
						p(
							V,
							{ loading: _($).loading && !_($).data },
							{
								default: n(() => [
									s(E, { title: h.value, subtitle: k.value }, null, 8, [
										"title",
										"subtitle",
									]),
									a.value
										? (i(),
										  p(
												z,
												{ key: 0 },
												{
													main: n(() => [
														s(
															ge,
															{
																checkin: a.value.checkin,
																week: a.value.week,
																onChanged:
																	r[0] ||
																	(r[0] = (l) => _($).reload()),
															},
															null,
															8,
															["checkin", "week"],
														),
														o("div", fe, [
															(i(),
															u(
																C,
																null,
																w(x, (l) =>
																	s(
																		y,
																		{
																			key: l.label,
																			to: l.to,
																			class: "flex items-center gap-2.5 rounded-lg border border-outline-gray-1 bg-surface-white p-3 transition-colors hover:bg-surface-gray-1",
																		},
																		{
																			default: n(() => [
																				o("span", he, [
																					s(
																						_(R),
																						{
																							name: l.icon,
																							class: "h-3.5 w-3.5",
																						},
																						null,
																						8,
																						["name"],
																					),
																				]),
																				o(
																					"span",
																					pe,
																					d(l.label),
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
														s(
															b,
															{ title: "My Requests", padded: !1 },
															{
																action: n(() => [
																	s(_(L), {
																		variant: "ghost",
																		route: "/leave",
																		label: "View All",
																	}),
																]),
																default: n(() => [
																	s(
																		F,
																		{
																			columns: c,
																			rows: a.value.requests,
																			"empty-message":
																				"You have not raised any requests yet.",
																		},
																		{
																			"cell-detail": n(
																				({ row: l }) => [
																					o(
																						"span",
																						ke,
																						d(f(l)),
																						1,
																					),
																				],
																			),
																			"cell-submitted": n(
																				({ row: l }) => [
																					o(
																						"span",
																						ye,
																						d(
																							_(Y)(
																								l.submitted,
																							),
																						),
																						1,
																					),
																				],
																			),
																			"cell-approver": n(
																				({ row: l }) => [
																					o(
																						"span",
																						ve,
																						d(
																							l.approver_name ||
																								"—",
																						),
																						1,
																					),
																				],
																			),
																			"cell-status": n(
																				({ row: l }) => [
																					s(
																						O,
																						{
																							status: l.status,
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
													]),
													side: n(() => {
														var l;
														return [
															(l = a.value.pending_approvals) !=
																null && l.length
																? (i(),
																  p(
																		b,
																		{
																			key: 0,
																			title: "Waiting on You",
																		},
																		{
																			action: n(() => [
																				s(
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
																			default: n(() => [
																				o("ul", be, [
																					(i(!0),
																					u(
																						C,
																						null,
																						w(
																							a.value
																								.pending_approvals,
																							(
																								t,
																							) => (
																								i(),
																								u(
																									"li",
																									{
																										key: t.name,
																										class: "flex items-center justify-between gap-2",
																									},
																									[
																										s(
																											D,
																											{
																												name: t.employee_name,
																												meta: `${t.type}, ${t.detail}`,
																												size: "md",
																											},
																											null,
																											8,
																											[
																												"name",
																												"meta",
																											],
																										),
																										s(
																											_(
																												R,
																											),
																											{
																												name: "chevron-right",
																												class: "h-3.5 w-3.5 shrink-0 text-ink-gray-4",
																											},
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
																		},
																  ))
																: A("", !0),
															s(
																b,
																{
																	title: "Leave Balance",
																	action: "Apply",
																	onAction:
																		r[1] ||
																		(r[1] = (t) =>
																			e.$router.push(
																				"/leave",
																			)),
																},
																{
																	default: n(() => [
																		s(
																			G,
																			{
																				balances:
																					a.value
																						.balances,
																			},
																			null,
																			8,
																			["balances"],
																		),
																	]),
																	_: 1,
																},
															),
															s(
																b,
																{ title: "Out Today" },
																{
																	action: n(() => [
																		o(
																			"span",
																			xe,
																			d(
																				a.value.out_today
																					.count,
																			) +
																				" of " +
																				d(
																					a.value
																						.out_today
																						.total,
																				),
																			1,
																		),
																	]),
																	default: n(() => [
																		a.value.out_today.people
																			.length
																			? (i(),
																			  u("ul", $e, [
																					(i(!0),
																					u(
																						C,
																						null,
																						w(
																							a.value
																								.out_today
																								.people,
																							(
																								t,
																							) => (
																								i(),
																								u(
																									"li",
																									{
																										key: t.employee,
																										class: "flex items-center justify-between gap-2",
																									},
																									[
																										s(
																											D,
																											{
																												name: t.employee_name,
																												to: `/directory/${t.employee}`,
																												size: "md",
																											},
																											null,
																											8,
																											[
																												"name",
																												"to",
																											],
																										),
																										s(
																											O,
																											{
																												status: "on leave",
																												label: t.reason,
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
																			: (i(),
																			  p(T, {
																					key: 1,
																					message:
																						"Everybody is in today.",
																			  })),
																	]),
																	_: 1,
																},
															),
															s(
																b,
																{ title: "Coming Up" },
																{
																	default: n(() => [
																		a.value.coming_up.length
																			? (i(),
																			  u("dl", Ce, [
																					(i(!0),
																					u(
																						C,
																						null,
																						w(
																							a.value
																								.coming_up,
																							(
																								t,
																							) => (
																								i(),
																								p(
																									H,
																									{
																										key:
																											t.date +
																											t.label,
																										label: g(
																											t.date,
																										),
																										value: t.label,
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
																			: (i(),
																			  p(T, {
																					key: 1,
																					message:
																						"Nothing in the next 60 days.",
																			  })),
																	]),
																	_: 1,
																},
															),
														];
													}),
													_: 1,
												},
										  ))
										: A("", !0),
								]),
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
export { Re as default };
