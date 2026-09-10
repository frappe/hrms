import { a as $, _ as f, b as H } from "./SectionCard-C5Qs8pBJ.js";
import { _ as N } from "./DashGrid-CGnJY6QD.js";
import { _ as B } from "./DataTable-BPI_hH2T.js";
import { _ as C } from "./StatTiles-CcQndbp7.js";
import { _ as m } from "./StatusBadge-sSVuNJEI.js";
import { _ as y } from "./FieldRow-DoxIhPye.js";
import { q as c, d as p } from "./index-BSaIzYPn.js";
import {
	L as D,
	o,
	d as r,
	w as l,
	f as t,
	h as L,
	e as s,
	t as i,
	g as u,
	z as b,
	s as g,
	F,
	a as v,
} from "./frappe-ui-D0k6koYp.js";
import "./EmptyState-38_uLDf3.js";
const R = { class: "text-ink-gray-5" },
	V = { class: "flex flex-col" },
	z = { class: "flex flex-col gap-0.5" },
	M = { class: "text-p-base-semibold text-ink-gray-9" },
	O = { class: "nums text-base text-ink-gray-5" },
	G = {
		__name: "Holidays",
		setup(T) {
			const x = [
					{ key: "date", label: "Date", nums: !0 },
					{ key: "weekday", label: "Day", hideOnMobile: !0 },
					{ key: "description", label: "Occasion", primary: !0 },
					{ key: "flag", label: "", align: "right", badge: !0 },
				],
				a = v(() => c.data),
				h = v(() => {
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
						H,
						{ loading: u(c).loading && !u(c).data },
						{
							default: l(() => {
								var d;
								return [
									t(
										$,
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
										  L(
												F,
												{ key: 0 },
												[
													t(C, { tiles: h.value }, null, 8, ["tiles"]),
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
																			B,
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
																								class: g(
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
																									class: g(
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
																				s("div", z, [
																					s(
																						"span",
																						M,
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
																						O,
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
																: b("", !0),
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
					)
				)
			);
		},
	};
export { G as default };
