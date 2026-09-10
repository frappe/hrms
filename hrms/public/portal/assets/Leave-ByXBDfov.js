import {
	L as N,
	o,
	h as m,
	f as t,
	w as l,
	g as n,
	I as B,
	k as y,
	F as _,
	d as v,
	z as b,
	i as D,
	e as k,
	t as c,
	a as g,
	B as L,
	b as A,
} from "./frappe-ui-D0k6koYp.js";
import { a as C, _ as d, b as M } from "./SectionCard-C5Qs8pBJ.js";
import { _ as V } from "./DashGrid-CGnJY6QD.js";
import { _ as R } from "./DataTable-BPI_hH2T.js";
import { _ as S } from "./StatTiles-CcQndbp7.js";
import { _ as T } from "./StatusBadge-sSVuNJEI.js";
import { _ as z } from "./PersonRow-2k8WhDWN.js";
import { _ as F } from "./BalanceBars-9ROF_iIl.js";
import { _ as O } from "./EmptyState-38_uLDf3.js";
import { _ as j, r as q } from "./RequestDialog-UMsP4D4j.js";
import { l as p, b as $ } from "./index-BSaIzYPn.js";
import "./RequestField-CEA0aLLd.js";
import "./DateField-DafgtgxX.js";
import "./toast-BPVivXt-.js";
const E = { class: "text-ink-gray-6" },
	I = { key: 0, class: "flex flex-col gap-2" },
	P = { class: "nums shrink-0 text-base text-ink-gray-5" },
	oe = {
		__name: "Leave",
		setup(U) {
			const h = [
					{ key: "leave_type", label: "Type", primary: !0 },
					{ key: "dates", label: "Dates", nums: !0 },
					{ key: "total_leave_days", label: "Days", nums: !0, hideOnMobile: !0 },
					{ key: "approver_name", label: "Approver", hideOnMobile: !0 },
					{ key: "display_status", label: "Status", align: "right", badge: !0 },
				],
				x = A(),
				u = L(!1),
				s = g(() => p.data),
				f = g(() => {
					var i;
					return (((i = s.value) == null ? void 0 : i.balances) || [])
						.slice(0, 4)
						.map((a) => ({
							label: a.leave_type,
							value: a.balance,
							pct: a.pct,
							hint: `of ${a.allocated} allocated`,
						}));
				});
			function w(i) {
				x.push(q("leave", i.name));
			}
			return (
				N(() => p.fetch()),
				(i, a) => (
					o(),
					m(
						_,
						null,
						[
							t(
								M,
								{ loading: n(p).loading && !n(p).data },
								{
									default: l(() => {
										var r;
										return [
											t(
												C,
												{
													title: "Leave",
													subtitle:
														(r = s.value) != null &&
														r.allocation_period
															? `Allocation period ${s.value.allocation_period}`
															: "",
												},
												{
													actions: l(() => [
														t(
															n(B),
															{
																variant: "solid",
																onClick:
																	a[0] ||
																	(a[0] = (e) => (u.value = !0)),
															},
															{
																default: l(() => [
																	...(a[3] ||
																		(a[3] = [
																			y(
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
											s.value
												? (o(),
												  m(
														_,
														{ key: 0 },
														[
															f.value.length
																? (o(),
																  v(
																		S,
																		{ key: 0, tiles: f.value },
																		null,
																		8,
																		["tiles"],
																  ))
																: b("", !0),
															t(V, null, {
																main: l(() => [
																	t(
																		d,
																		{
																			title: "My Applications",
																			padded: !1,
																		},
																		{
																			default: l(() => [
																				t(
																					R,
																					{
																						columns: h,
																						rows: s
																							.value
																							.applications,
																						clickable:
																							"",
																						"empty-message":
																							"You have not applied for leave yet.",
																						onRowClick:
																							w,
																					},
																					{
																						"cell-dates":
																							l(
																								({
																									row: e,
																								}) => [
																									y(
																										c(
																											n(
																												$,
																											)(
																												e.from_date,
																												e.to_date,
																											),
																										),
																										1,
																									),
																								],
																							),
																						"cell-approver_name":
																							l(
																								({
																									row: e,
																								}) => [
																									k(
																										"span",
																										E,
																										c(
																											e.approver_name ||
																												"—",
																										),
																										1,
																									),
																								],
																							),
																						"cell-display_status":
																							l(
																								({
																									row: e,
																								}) => [
																									t(
																										T,
																										{
																											status: e.display_status,
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
																side: l(() => [
																	t(
																		d,
																		{ title: "Balance" },
																		{
																			default: l(() => [
																				t(
																					F,
																					{
																						balances:
																							s.value
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
																	t(
																		d,
																		{
																			title: "Team, Next 7 Days",
																		},
																		{
																			default: l(() => [
																				s.value.team.length
																					? (o(),
																					  m("ul", I, [
																							(o(!0),
																							m(
																								_,
																								null,
																								D(
																									s
																										.value
																										.team,
																									(
																										e,
																									) => (
																										o(),
																										m(
																											"li",
																											{
																												key:
																													e.employee +
																													e.from_date,
																												class: "flex items-center justify-between gap-2",
																											},
																											[
																												t(
																													z,
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
																												k(
																													"span",
																													P,
																													c(
																														n(
																															$,
																														)(
																															e.from_date,
																															e.to_date,
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
																					  v(O, {
																							key: 1,
																							message:
																								"Nobody is away in the next week.",
																					  })),
																			]),
																			_: 1,
																		},
																	),
																]),
																_: 1,
															}),
														],
														64,
												  ))
												: b("", !0),
										];
									}),
									_: 1,
								},
								8,
								["loading"],
							),
							t(
								j,
								{
									open: u.value,
									"onUpdate:open": a[1] || (a[1] = (r) => (u.value = r)),
									type: "leave",
									onSaved: a[2] || (a[2] = (r) => n(p).fetch()),
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
export { oe as default };
