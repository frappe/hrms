import {
	L as B,
	o,
	d as v,
	w as t,
	f as l,
	h as m,
	e as i,
	t as r,
	s as F,
	g as n,
	k as T,
	z as b,
	F as V,
	a as k,
	b as A,
} from "./frappe-ui-rHlwnvVy.js";
import { a as S, _ as w, b as z } from "./SectionCard-0tgyDAFI.js";
import { _ as $ } from "./DataTable-BY05XQx8.js";
import { _ as D } from "./StatTiles-DcUJsMoQ.js";
import { _ as C } from "./StatusBadge-ZWn2FvVw.js";
import { _ as p } from "./Score-BvtjKy2-.js";
import { k as u, a as d, d as g } from "./index-6wvshjQq.js";
import "./EmptyState-0_BFjfJU.js";
const E = { class: "text-ink-gray-8" },
	L = { class: "nums text-ink-gray-5" },
	H = { class: "nums text-ink-gray-8" },
	I = { class: "font-semibold text-ink-gray-9" },
	P = { key: 0, class: "text-ink-gray-4" },
	Z = {
		__name: "Appraisals",
		setup(U) {
			const x = [
					{ key: "cycle", label: "Cycle", primary: !0 },
					{ key: "year", label: "Year", nums: !0, muted: !0, hideOnMobile: !0 },
					{
						key: "self_score",
						label: "Self",
						align: "right",
						nums: !0,
						hideOnMobile: !0,
					},
					{
						key: "feedback_score",
						label: "Feedback",
						align: "right",
						nums: !0,
						hideOnMobile: !0,
					},
					{ key: "final_score", label: "Final", align: "right", nums: !0 },
					{ key: "status", label: "Status", align: "right", badge: !0 },
				],
				M = [
					{ key: "from_date", label: "Effective", primary: !0 },
					{
						key: "base",
						label: "Monthly",
						align: "right",
						nums: !0,
						muted: !0,
						hideOnMobile: !0,
					},
					{ key: "annual", label: "CTC", align: "right", nums: !0 },
					{ key: "change", label: "Change", align: "right", nums: !0 },
				],
				Y = A(),
				s = k(() => u.data),
				N = k(() => {
					var _, e, f, y, h;
					const a = ((_ = s.value) == null ? void 0 : _.stats) || {};
					return [
						{
							label: "Latest score",
							value: a.latest_score ? `${a.latest_score} / 5` : "—",
							hint: a.latest_cycle || "No review yet",
						},
						{
							label: "Average score",
							value: a.average_score ? `${a.average_score} / 5` : "—",
							hint: a.reviews
								? `${a.reviews} review${a.reviews === 1 ? "" : "s"}`
								: "",
						},
						{
							label: "Current CTC",
							value: d(a.current_ctc, { compact: !0 }),
							hint: a.current_since ? `since ${g(a.current_since, "MMM YYYY")}` : "",
						},
						{
							label: "Total growth",
							value:
								(f = (e = s.value) == null ? void 0 : e.growth) != null &&
								f.total_pct
									? `${c(s.value.growth.total_pct)}%`
									: "—",
							hint:
								(h = (y = s.value) == null ? void 0 : y.growth) != null &&
								h.annual_pct
									? `${c(s.value.growth.annual_pct)}% a year`
									: "",
						},
					];
				});
			function c(a) {
				return `${a > 0 ? "+" : ""}${a}`;
			}
			function O(a) {
				return a > 0 ? "text-ink-green-3" : a < 0 ? "text-ink-red-3" : "text-ink-gray-6";
			}
			function R(a) {
				Y.push(`/appraisals/${encodeURIComponent(a.name)}`);
			}
			return (
				B(() => u.fetch()),
				(a, _) => (
					o(),
					v(
						z,
						{ loading: n(u).loading && !n(u).data },
						{
							default: t(() => [
								l(S, {
									title: "Appraisals",
									subtitle: "Your reviews and how your pay has moved",
								}),
								s.value
									? (o(),
									  m(
											V,
											{ key: 0 },
											[
												l(D, { tiles: N.value }, null, 8, ["tiles"]),
												l(
													w,
													{ title: "Review History", padded: !1 },
													{
														default: t(() => [
															l(
																$,
																{
																	columns: x,
																	rows: s.value.appraisals,
																	clickable: "",
																	"empty-message":
																		"You have not been appraised yet.",
																	onRowClick: R,
																},
																{
																	"cell-cycle": t(
																		({ row: e }) => [
																			i(
																				"span",
																				E,
																				r(e.cycle),
																				1,
																			),
																		],
																	),
																	"cell-year": t(
																		({ row: e }) => [
																			i(
																				"span",
																				L,
																				r(e.year || "—"),
																				1,
																			),
																		],
																	),
																	"cell-final_score": t(
																		({ row: e }) => [
																			l(
																				p,
																				{
																					value: e.final_score,
																					strong: "",
																				},
																				null,
																				8,
																				["value"],
																			),
																		],
																	),
																	"cell-self_score": t(
																		({ row: e }) => [
																			l(
																				p,
																				{
																					value: e.self_score,
																				},
																				null,
																				8,
																				["value"],
																			),
																		],
																	),
																	"cell-feedback_score": t(
																		({ row: e }) => [
																			l(
																				p,
																				{
																					value: e.feedback_score,
																				},
																				null,
																				8,
																				["value"],
																			),
																		],
																	),
																	"cell-status": t(
																		({ row: e }) => [
																			l(
																				C,
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
												l(
													w,
													{ title: "Pay Revisions", padded: !1 },
													{
														action: t(() => [
															s.value.growth.total_pct
																? (o(),
																  v(
																		C,
																		{
																			key: 0,
																			status: "approved",
																			label: `${c(
																				s.value.growth
																					.total_pct,
																			)}% since ${n(g)(
																				s.value.growth
																					.from_date,
																				"MMM YYYY",
																			)}`,
																		},
																		null,
																		8,
																		["label"],
																  ))
																: b("", !0),
														]),
														default: t(() => [
															l(
																$,
																{
																	columns: M,
																	rows: s.value.compensation,
																	"empty-message":
																		"No salary structure has been assigned yet.",
																},
																{
																	"cell-from_date": t(
																		({ row: e }) => [
																			i(
																				"span",
																				H,
																				r(
																					n(g)(
																						e.from_date,
																					),
																				),
																				1,
																			),
																		],
																	),
																	"cell-base": t(
																		({ row: e }) => [
																			T(r(n(d)(e.base)), 1),
																		],
																	),
																	"cell-annual": t(
																		({ row: e }) => [
																			i(
																				"span",
																				I,
																				r(n(d)(e.annual)),
																				1,
																			),
																		],
																	),
																	"cell-change": t(
																		({ row: e }) => [
																			e.change_pct === null
																				? (o(),
																				  m(
																						"span",
																						P,
																						"—",
																				  ))
																				: (o(),
																				  m(
																						"span",
																						{
																							key: 1,
																							class: F(
																								[
																									"nums",
																									O(
																										e.change_pct,
																									),
																								],
																							),
																						},
																						r(
																							c(
																								e.change_pct,
																							),
																						) + "% ",
																						3,
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
											],
											64,
									  ))
									: b("", !0),
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
export { Z as default };
