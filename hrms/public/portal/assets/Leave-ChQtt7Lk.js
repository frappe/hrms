import {
	L as N,
	o,
	i as m,
	f as t,
	w as s,
	h as n,
	I as B,
	l as f,
	F as _,
	e as y,
	z as v,
	j as D,
	g as k,
	t as d,
	a as g,
	B as L,
	b as A,
} from "./frappe-ui-CXkWuvNK.js";
import { a as C, _ as b, b as M } from "./SectionCard-BKeIA1B1.js";
import { _ as V } from "./DashGrid-CcXWxztj.js";
import { _ as R } from "./DataTable-KquPBl5L.js";
import { _ as S } from "./StatTiles-knaJnTjR.js";
import { _ as T } from "./StatusBadge-DcMGXIA6.js";
import { _ as j } from "./PersonRow-BtXbdUjH.js";
import { _ as z } from "./EmptyState-DhAxAin0.js";
import { _ as F, r as O } from "./RequestDialog-DuFWjain.js";
import { l as p, a as $ } from "./index-BpEXs0_U.js";
import "./RequestField-B8HqhQXt.js";
import "./DateField-BLUeL_2-.js";
import "./toast-Ca-cKV9o.js";
const q = { class: "text-ink-gray-6" },
	E = { key: 0, class: "flex flex-col gap-2" },
	I = { class: "nums shrink-0 text-base text-ink-gray-5" },
	se = {
		__name: "Leave",
		setup(P) {
			const h = [
					{ key: "leave_type", label: "Type", primary: !0 },
					{ key: "dates", label: "Dates", nums: !0 },
					{ key: "total_leave_days", label: "Days", nums: !0, hideOnMobile: !0 },
					{ key: "approver_name", label: "Approver", hideOnMobile: !0 },
					{ key: "display_status", label: "Status", align: "right", badge: !0 },
				],
				x = A(),
				u = L(!1),
				l = g(() => p.data),
				c = g(() => {
					var i;
					return (((i = l.value) == null ? void 0 : i.balances) || [])
						.slice(0, 4)
						.map((a) => ({
							label: a.leave_type,
							value: a.balance,
							pct: a.pct,
							hint: `of ${a.allocated} allocated`,
						}));
				});
			function w(i) {
				x.push(O("leave", i.name));
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
									default: s(() => {
										var r;
										return [
											t(
												C,
												{
													title: "Leave",
													subtitle:
														(r = l.value) != null &&
														r.allocation_period
															? `Allocation period ${l.value.allocation_period}`
															: "",
												},
												{
													actions: s(() => [
														t(
															n(B),
															{
																variant: "solid",
																onClick:
																	a[0] ||
																	(a[0] = (e) => (u.value = !0)),
															},
															{
																default: s(() => [
																	...(a[3] ||
																		(a[3] = [
																			f(
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
												? (o(),
												  m(
														_,
														{ key: 0 },
														[
															c.value.length
																? (o(),
																  y(
																		S,
																		{ key: 0, tiles: c.value },
																		null,
																		8,
																		["tiles"],
																  ))
																: v("", !0),
															t(V, null, {
																main: s(() => [
																	t(
																		b,
																		{
																			title: "My Applications",
																			padded: !1,
																		},
																		{
																			default: s(() => [
																				t(
																					R,
																					{
																						columns: h,
																						rows: l
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
																							s(
																								({
																									row: e,
																								}) => [
																									f(
																										d(
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
																							s(
																								({
																									row: e,
																								}) => [
																									k(
																										"span",
																										q,
																										d(
																											e.approver_name ||
																												"—",
																										),
																										1,
																									),
																								],
																							),
																						"cell-display_status":
																							s(
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
																side: s(() => [
																	t(
																		b,
																		{
																			title: "Team, Next 7 Days",
																		},
																		{
																			default: s(() => [
																				l.value.team.length
																					? (o(),
																					  m("ul", E, [
																							(o(!0),
																							m(
																								_,
																								null,
																								D(
																									l
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
																													j,
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
																													I,
																													d(
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
																					  y(z, {
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
												: v("", !0),
										];
									}),
									_: 1,
								},
								8,
								["loading"],
							),
							t(
								F,
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
export { se as default };
