import {
	b as D,
	P as M,
	o as r,
	s as i,
	h as a,
	g as t,
	i as u,
	M as A,
	B as g,
	F as c,
	f as p,
	C as y,
	t as h,
	k as v,
	x as k,
	a as x,
	e as L,
} from "./frappe-ui-BQ9PgXrr.js";
import { _ as d, a as R } from "./SectionCard-u_7VCKnT.js";
import { _ as T } from "./PageHead-3jtDpZ9g.js";
import { _ as V } from "./DashGrid-Bd23iLvt.js";
import { _ as P } from "./DataTable-vZ6Z-J3d.js";
import { _ as S } from "./StatTiles-YoNxs_Qn.js";
import { _ as j } from "./StatusBadge-Bqz4zlkD.js";
import { _ as F } from "./PersonRow-DZ4YBxpS.js";
import { _ as O } from "./BalanceBars-CBgUe-mJ.js";
import { _ as q } from "./FieldRow-DbBPtAxY.js";
import { _ as z } from "./EmptyState-DNwecFw5.js";
import { _ as E, r as U } from "./RequestDialog-TPB8mqrQ.js";
import { l as _, c as $ } from "./index-DKSqIuAQ.js";
import "./toast-9qekBDJT.js";
const Y = { class: "text-ink-gray-6" },
	G = { key: 0, class: "flex flex-col gap-2" },
	H = { class: "nums shrink-0 text-base text-ink-gray-5" },
	I = { class: "flex flex-col" },
	ue = {
		__name: "Leave",
		setup(J) {
			const w = [
					{ key: "leave_type", label: "Type", primary: !0 },
					{ key: "dates", label: "Dates", nums: !0 },
					{ key: "total_leave_days", label: "Days", nums: !0, hideOnMobile: !0 },
					{ key: "approver_name", label: "Approver", hideOnMobile: !0 },
					{ key: "display_status", label: "Status", align: "right", badge: !0 },
				],
				N = D(),
				f = L(!1),
				l = x(() => _.data),
				b = x(() => {
					var s;
					return (((s = l.value) == null ? void 0 : s.balances) || [])
						.slice(0, 4)
						.map((e) => ({
							label: e.leave_type,
							value: e.balance,
							pct: e.pct,
							hint: `of ${e.allocated} allocated`,
						}));
				});
			function B(s) {
				const e = [];
				return (
					s.max_continuous && e.push(`max ${s.max_continuous} days at a stretch`),
					s.carry_forward && e.push("carries forward"),
					s.optional && e.push("optional"),
					e.length ? e.join(", ") : "No special rules"
				);
			}
			function C(s) {
				N.push(U("leave", s.name));
			}
			return (
				M(() => _.fetch()),
				(s, e) => (
					r(),
					i(
						c,
						null,
						[
							a(
								R,
								{ loading: u(_).loading && !u(_).data },
								{
									default: t(() => {
										var m;
										return [
											a(
												T,
												{
													title: "Leave",
													subtitle:
														(m = l.value) != null &&
														m.allocation_period
															? `Allocation period ${l.value.allocation_period}`
															: "",
												},
												{
													actions: t(() => [
														a(
															u(A),
															{
																variant: "solid",
																onClick:
																	e[0] ||
																	(e[0] = (o) => (f.value = !0)),
															},
															{
																default: t(() => [
																	...(e[3] ||
																		(e[3] = [
																			g(
																				"Apply for Leave",
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
												8,
												["subtitle"],
											),
											l.value
												? (r(),
												  i(
														c,
														{ key: 0 },
														[
															b.value.length
																? (r(),
																  p(
																		S,
																		{ key: 0, tiles: b.value },
																		null,
																		8,
																		["tiles"],
																  ))
																: y("", !0),
															a(V, null, {
																main: t(() => [
																	a(
																		d,
																		{
																			title: "My Applications",
																			padded: !1,
																		},
																		{
																			default: t(() => [
																				a(
																					P,
																					{
																						columns: w,
																						rows: l
																							.value
																							.applications,
																						clickable:
																							"",
																						"empty-message":
																							"You have not applied for leave yet.",
																						onRowClick:
																							C,
																					},
																					{
																						"cell-dates":
																							t(
																								({
																									row: o,
																								}) => [
																									g(
																										k(
																											u(
																												$,
																											)(
																												o.from_date,
																												o.to_date,
																											),
																										),
																										1,
																									),
																								],
																							),
																						"cell-approver_name":
																							t(
																								({
																									row: o,
																								}) => [
																									v(
																										"span",
																										Y,
																										k(
																											o.approver_name ||
																												"—",
																										),
																										1,
																									),
																								],
																							),
																						"cell-display_status":
																							t(
																								({
																									row: o,
																								}) => [
																									a(
																										j,
																										{
																											status: o.display_status,
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
																	),
																]),
																side: t(() => {
																	var o;
																	return [
																		a(
																			d,
																			{ title: "Balance" },
																			{
																				default: t(() => [
																					a(
																						O,
																						{
																							balances:
																								l
																									.value
																									.balances,
																						},
																						null,
																						8,
																						[
																							"balances",
																						],
																					),
																				]),
																				_: 1,
																			},
																		),
																		a(
																			d,
																			{
																				title: "Team, Next 7 Days",
																			},
																			{
																				default: t(() => [
																					l.value.team
																						.length
																						? (r(),
																						  i(
																								"ul",
																								G,
																								[
																									(r(
																										!0,
																									),
																									i(
																										c,
																										null,
																										h(
																											l
																												.value
																												.team,
																											(
																												n,
																											) => (
																												r(),
																												i(
																													"li",
																													{
																														key:
																															n.employee +
																															n.from_date,
																														class: "flex items-center justify-between gap-2",
																													},
																													[
																														a(
																															F,
																															{
																																name: n.employee_name,
																																to: `/directory/${n.employee}`,
																																size: "md",
																															},
																															null,
																															8,
																															[
																																"name",
																																"to",
																															],
																														),
																														v(
																															"span",
																															H,
																															k(
																																u(
																																	$,
																																)(
																																	n.from_date,
																																	n.to_date,
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
																								],
																						  ))
																						: (r(),
																						  p(z, {
																								key: 1,
																								message:
																									"Nobody is away in the next week.",
																						  })),
																				]),
																				_: 1,
																			},
																		),
																		(o = l.value.policy) !=
																			null && o.length
																			? (r(),
																			  p(
																					d,
																					{
																						key: 0,
																						title: "Rules",
																						"readonly-label":
																							"Per leave type",
																					},
																					{
																						default: t(
																							() => [
																								v(
																									"dl",
																									I,
																									[
																										(r(
																											!0,
																										),
																										i(
																											c,
																											null,
																											h(
																												l
																													.value
																													.policy,
																												(
																													n,
																												) => (
																													r(),
																													p(
																														q,
																														{
																															key: n.leave_type,
																															label: n.leave_type,
																															value: B(
																																n,
																															),
																															locked: "",
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
																									],
																								),
																							],
																						),
																						_: 1,
																					},
																			  ))
																			: y("", !0),
																	];
																}),
																_: 1,
															}),
														],
														64,
												  ))
												: y("", !0),
										];
									}),
									_: 1,
								},
								8,
								["loading"],
							),
							a(
								E,
								{
									open: f.value,
									"onUpdate:open": e[1] || (e[1] = (m) => (f.value = m)),
									type: "leave",
									onSaved: e[2] || (e[2] = (m) => u(_).fetch()),
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
export { ue as default };
