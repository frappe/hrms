import {
	v as R,
	o as t,
	d as o,
	w as l,
	h as i,
	f as s,
	g as d,
	e as u,
	F as _,
	i as p,
	z as r,
	t as n,
	k as g,
	u as S,
	a as v,
} from "./frappe-ui-rHlwnvVy.js";
import { a as C, _ as c, b as F } from "./SectionCard-0tgyDAFI.js";
import { _ as G } from "./DashGrid-Cmnm2mAO.js";
import { _ as k } from "./DataTable-BY05XQx8.js";
import { _ as A } from "./StatTiles-DcUJsMoQ.js";
import { _ as B } from "./StatusBadge-ZWn2FvVw.js";
import { _ as N } from "./FieldRow-C13lI4HG.js";
import { _ as h } from "./TotalRow-DkNHj82l.js";
import { _ as V } from "./PersonRow-LB2-2vnj.js";
import { _ as f } from "./Score-BvtjKy2-.js";
import { n as m, b as z, d as D } from "./index-6wvshjQq.js";
import "./EmptyState-0_BFjfJU.js";
const E = { class: "nums font-semibold text-ink-gray-9" },
	K = { class: "flex flex-col gap-3" },
	M = { class: "flex flex-wrap items-baseline justify-between gap-2" },
	O = { key: 0, class: "mt-2 whitespace-pre-line text-p-base text-ink-gray-7" },
	W = { key: 1, class: "mt-1 text-sm text-ink-gray-5" },
	j = { class: "flex flex-col" },
	L = { class: "whitespace-pre-line text-p-base text-ink-gray-7" },
	te = {
		__name: "Appraisal",
		setup(T) {
			const y = [
					{ key: "kra", label: "KRA", primary: !0 },
					{ key: "weightage", label: "Weight", align: "right", nums: !0, muted: !0 },
					{
						key: "completion",
						label: "Completion",
						align: "right",
						nums: !0,
						hideOnMobile: !0,
					},
					{ key: "score", label: "Score", align: "right", nums: !0 },
				],
				$ = [
					{ key: "kra", label: "Goal", primary: !0 },
					{ key: "weightage", label: "Weight", align: "right", nums: !0, muted: !0 },
					{ key: "score", label: "Rated", align: "right", nums: !0, hideOnMobile: !0 },
					{ key: "earned", label: "Earned", align: "right", nums: !0 },
				],
				w = S(),
				e = v(() => m.data),
				x = v(() => [
					{ label: "Final score", value: `${e.value.final_score} / 5` },
					{
						label: "Goal score",
						value: e.value.goal_score ? `${e.value.goal_score} / 5` : "—",
					},
					{
						label: "Self score",
						value: e.value.self_score ? `${e.value.self_score} / 5` : "—",
					},
					{
						label: "Feedback",
						value: e.value.feedback_score ? `${e.value.feedback_score} / 5` : "—",
						hint: e.value.feedback.length
							? `${e.value.feedback.length} reviewer${
									e.value.feedback.length === 1 ? "" : "s"
							  }`
							: "",
					},
				]);
			return (
				R(
					() => w.params.name,
					(b) => m.fetch({ name: b }),
					{ immediate: !0 },
				),
				(b, Y) => (
					t(),
					o(
						F,
						{ loading: d(m).loading && !d(m).data },
						{
							default: l(() => [
								e.value
									? (t(),
									  i(
											_,
											{ key: 0 },
											[
												s(
													C,
													{
														subtitle: `${d(z)(
															e.value.start_date,
															e.value.end_date,
														)} · ${e.value.designation || ""}`,
														crumbs: [
															{
																label: "Appraisals",
																to: "/appraisals",
															},
															{ label: e.value.cycle },
														],
													},
													{
														actions: l(() => [
															s(
																B,
																{ status: e.value.status },
																null,
																8,
																["status"],
															),
														]),
														_: 1,
													},
													8,
													["subtitle", "crumbs"],
												),
												s(A, { tiles: x.value }, null, 8, ["tiles"]),
												s(G, null, {
													main: l(() => [
														e.value.kras.length
															? (t(),
															  o(
																	c,
																	{
																		key: 0,
																		title: "KRAs",
																		"readonly-label":
																			"Scored from goals",
																		padded: !1,
																	},
																	{
																		default: l(() => [
																			s(
																				k,
																				{
																					columns: y,
																					rows: e.value
																						.kras,
																					"id-key":
																						"kra",
																				},
																				{
																					"cell-weightage":
																						l(
																							({
																								row: a,
																							}) => [
																								g(
																									n(
																										a.weightage,
																									) +
																										"%",
																									1,
																								),
																							],
																						),
																					"cell-completion":
																						l(
																							({
																								row: a,
																							}) => [
																								g(
																									n(
																										a.completion,
																									) +
																										"%",
																									1,
																								),
																							],
																						),
																					"cell-score":
																						l(
																							({
																								row: a,
																							}) => [
																								s(
																									f,
																									{
																										value: a.score,
																										strong: "",
																									},
																									null,
																									8,
																									[
																										"value",
																									],
																								),
																							],
																						),
																					_: 1,
																				},
																				8,
																				["rows"],
																			),
																			s(
																				h,
																				{
																					label: "Goal Score",
																					value: `${e.value.goal_score} / 5`,
																				},
																				null,
																				8,
																				["value"],
																			),
																		]),
																		_: 1,
																	},
															  ))
															: r("", !0),
														e.value.goals.length
															? (t(),
															  o(
																	c,
																	{
																		key: 1,
																		title: "Goals",
																		"readonly-label": e.value
																			.rated_manually
																			? "Rated by your manager"
																			: null,
																		padded: !1,
																	},
																	{
																		default: l(() => [
																			s(
																				k,
																				{
																					columns: $,
																					rows: e.value
																						.goals,
																					"id-key":
																						"kra",
																				},
																				{
																					"cell-weightage":
																						l(
																							({
																								row: a,
																							}) => [
																								g(
																									n(
																										a.weightage,
																									) +
																										"%",
																									1,
																								),
																							],
																						),
																					"cell-score":
																						l(
																							({
																								row: a,
																							}) => [
																								s(
																									f,
																									{
																										value: a.score,
																									},
																									null,
																									8,
																									[
																										"value",
																									],
																								),
																							],
																						),
																					"cell-earned":
																						l(
																							({
																								row: a,
																							}) => [
																								u(
																									"span",
																									E,
																									n(
																										a.earned,
																									),
																									1,
																								),
																							],
																						),
																					_: 1,
																				},
																				8,
																				["rows"],
																			),
																			s(
																				h,
																				{
																					label: "Goal Score",
																					value: `${e.value.goal_score} / 5`,
																				},
																				null,
																				8,
																				["value"],
																			),
																		]),
																		_: 1,
																	},
																	8,
																	["readonly-label"],
															  ))
															: r("", !0),
														e.value.feedback.length
															? (t(),
															  o(
																	c,
																	{ key: 2, title: "Feedback" },
																	{
																		default: l(() => [
																			u("ul", K, [
																				(t(!0),
																				i(
																					_,
																					null,
																					p(
																						e.value
																							.feedback,
																						(a) => (
																							t(),
																							i(
																								"li",
																								{
																									key: a.name,
																									class: "border-b border-outline-gray-1 pb-3 last:border-0 last:pb-0",
																								},
																								[
																									u(
																										"div",
																										M,
																										[
																											s(
																												V,
																												{
																													name: a.reviewer,
																													meta:
																														a.designation ||
																														"",
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
																												f,
																												{
																													value: a.score,
																													strong: "",
																												},
																												null,
																												8,
																												[
																													"value",
																												],
																											),
																										],
																									),
																									a.feedback
																										? (t(),
																										  i(
																												"p",
																												O,
																												n(
																													a.feedback,
																												),
																												1,
																										  ))
																										: r(
																												"",
																												!0,
																										  ),
																									a.added_on
																										? (t(),
																										  i(
																												"p",
																												W,
																												n(
																													d(
																														D,
																													)(
																														a.added_on,
																													),
																												),
																												1,
																										  ))
																										: r(
																												"",
																												!0,
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
															: r("", !0),
													]),
													side: l(() => [
														e.value.self_ratings.length
															? (t(),
															  o(
																	c,
																	{
																		key: 0,
																		title: "Self Rating",
																	},
																	{
																		default: l(() => [
																			u("dl", j, [
																				(t(!0),
																				i(
																					_,
																					null,
																					p(
																						e.value
																							.self_ratings,
																						(a) => (
																							t(),
																							o(
																								N,
																								{
																									key: a.criteria,
																									label: `${a.criteria} · ${a.weightage}%`,
																									value: `${a.rating} / 5`,
																									nums: "",
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
																			]),
																		]),
																		_: 1,
																	},
															  ))
															: r("", !0),
														e.value.reflections
															? (t(),
															  o(
																	c,
																	{
																		key: 1,
																		title: "Your Reflections",
																	},
																	{
																		default: l(() => [
																			u(
																				"p",
																				L,
																				n(
																					e.value
																						.reflections,
																				),
																				1,
																			),
																		]),
																		_: 1,
																	},
															  ))
															: r("", !0),
													]),
													_: 1,
												}),
											],
											64,
									  ))
									: r("", !0),
							]),
							_: 1,
						},
						8,
						["loading"],
					)
				)
			);
		},
	};
export { te as default };
