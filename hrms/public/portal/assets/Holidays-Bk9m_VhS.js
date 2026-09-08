import { _ as f, a as $ } from "./SectionCard-u_7VCKnT.js";
import { _ as H } from "./PageHead-3jtDpZ9g.js";
import { _ as N } from "./DashGrid-Bd23iLvt.js";
import { _ as C } from "./DataTable-vZ6Z-J3d.js";
import { _ as B } from "./StatTiles-YoNxs_Qn.js";
import { _ as m } from "./StatusBadge-Bqz4zlkD.js";
import { _ as y } from "./FieldRow-DbBPtAxY.js";
import { q as c, d as p } from "./index-DKSqIuAQ.js";
import {
	P as D,
	o,
	f as r,
	g as l,
	h as t,
	s as F,
	F as L,
	k as s,
	x as i,
	i as u,
	C as g,
	v,
	a as b,
} from "./frappe-ui-BQ9PgXrr.js";
import "./EmptyState-DNwecFw5.js";
const R = { class: "text-ink-gray-5" },
	V = { class: "flex flex-col" },
	M = { class: "flex flex-col gap-0.5" },
	O = { class: "text-p-base font-semibold text-ink-gray-9" },
	P = { class: "nums text-base text-ink-gray-5" },
	I = {
		__name: "Holidays",
		setup(T) {
			const x = [
					{ key: "date", label: "Date", nums: !0 },
					{ key: "weekday", label: "Day", hideOnMobile: !0 },
					{ key: "description", label: "Occasion", primary: !0 },
					{ key: "flag", label: "", align: "right", badge: !0 },
				],
				a = b(() => c.data),
				h = b(() => {
					var _, d, e, k;
					const n = ((_ = a.value) == null ? void 0 : _.stats) || {};
					return [
						{
							label: "Remaining",
							value: (d = n.remaining) != null ? d : 0,
							hint: n.next ? `next ${p(n.next.date)}` : "",
						},
						{
							label: "Total This Year",
							value: (e = n.total) != null ? e : 0,
							hint: "excluding weekly offs",
						},
						{
							label: "Lost to Weekends",
							value: (((k = a.value) == null ? void 0 : k.holidays) || []).filter(
								(w) => w.falls_on_off,
							).length,
							hint: "fall on a weekly off",
						},
					];
				});
			return (
				D(() => c.fetch()),
				(n, _) => (
					o(),
					r(
						$,
						{ loading: u(c).loading && !u(c).data },
						{
							default: l(() => {
								var d;
								return [
									t(
										H,
										{
											title: "Holidays",
											subtitle:
												((d = a.value) == null ? void 0 : d.list_name) ||
												"No holiday list assigned",
										},
										null,
										8,
										["subtitle"],
									),
									a.value
										? (o(),
										  F(
												L,
												{ key: 0 },
												[
													t(B, { tiles: h.value }, null, 8, ["tiles"]),
													t(N, null, {
														main: l(() => [
															t(
																f,
																{
																	title: "Holiday List",
																	"readonly-label": "HR-owned",
																	padded: !1,
																},
																{
																	default: l(() => [
																		t(
																			C,
																			{
																				columns: x,
																				rows: a.value
																					.holidays,
																				"id-key": "date",
																				"empty-message":
																					"No holidays configured for your list.",
																			},
																			{
																				"cell-date": l(
																					({
																						row: e,
																					}) => [
																						s(
																							"span",
																							{
																								class: v(
																									e.is_past &&
																										"text-ink-gray-5",
																								),
																							},
																							i(
																								u(
																									p,
																								)(
																									e.date,
																								),
																							),
																							3,
																						),
																					],
																				),
																				"cell-weekday": l(
																					({
																						row: e,
																					}) => [
																						s(
																							"span",
																							R,
																							i(
																								e.weekday,
																							),
																							1,
																						),
																					],
																				),
																				"cell-description":
																					l(
																						({
																							row: e,
																						}) => [
																							s(
																								"span",
																								{
																									class: v(
																										e.is_past &&
																											"text-ink-gray-5",
																									),
																								},
																								i(
																									e.description,
																								),
																								3,
																							),
																						],
																					),
																				"cell-flag": l(
																					({
																						row: e,
																					}) => [
																						e.falls_on_off
																							? (o(),
																							  r(
																									m,
																									{
																										key: 0,
																										status: "weekly off",
																										label: "Falls on a weekly off",
																									},
																							  ))
																							: e.is_past
																							  ? (o(),
																							    r(
																										m,
																										{
																											key: 1,
																											status: "taken",
																											label: "Past",
																										},
																							    ))
																							  : (o(),
																							    r(
																										m,
																										{
																											key: 2,
																											status: "available",
																											label: "Upcoming",
																										},
																							    )),
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
																f,
																{
																	title: "Your Calendar",
																	"readonly-label": "HR-owned",
																},
																{
																	default: l(() => [
																		s("dl", V, [
																			t(
																				y,
																				{
																					label: "Holiday list",
																					value: a.value
																						.list_name,
																					locked: "",
																				},
																				null,
																				8,
																				["value"],
																			),
																			t(
																				y,
																				{
																					label: "Weekly off",
																					value: a.value
																						.weekly_off,
																					locked: "",
																				},
																				null,
																				8,
																				["value"],
																			),
																			t(
																				y,
																				{
																					label: "Location",
																					value: a.value
																						.branch,
																					locked: "",
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
															a.value.stats.next
																? (o(),
																  r(
																		f,
																		{
																			key: 0,
																			title: "Next Holiday",
																		},
																		{
																			default: l(() => [
																				s("div", M, [
																					s(
																						"span",
																						O,
																						i(
																							a.value
																								.stats
																								.next
																								.description,
																						),
																						1,
																					),
																					s(
																						"span",
																						P,
																						i(
																							u(p)(
																								a
																									.value
																									.stats
																									.next
																									.date,
																							),
																						) +
																							" · " +
																							i(
																								a
																									.value
																									.stats
																									.next
																									.weekday,
																							),
																						1,
																					),
																				]),
																			]),
																			_: 1,
																		},
																  ))
																: g("", !0),
														]),
														_: 1,
													}),
												],
												64,
										  ))
										: g("", !0),
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
export { I as default };
