import {
	L as $,
	o as c,
	h as p,
	f as n,
	w as s,
	g as o,
	I as h,
	k as r,
	F as _,
	t as m,
	z as R,
	B as A,
	a as f,
	b as q,
} from "./frappe-ui-D0k6koYp.js";
import { a as x, _ as C, b as M } from "./SectionCard-C5Qs8pBJ.js";
import { _ as N } from "./DataTable-BPI_hH2T.js";
import { _ as O } from "./StatTiles-CcQndbp7.js";
import { _ as S } from "./StatusBadge-sSVuNJEI.js";
import { _ as w, r as B } from "./RequestDialog-UMsP4D4j.js";
import { j as l, a as u, d as D } from "./index-BSaIzYPn.js";
import "./EmptyState-38_uLDf3.js";
import "./RequestField-CEA0aLLd.js";
import "./DateField-DafgtgxX.js";
import "./toast-BPVivXt-.js";
const H = {
	__name: "Advances",
	setup(V) {
		const v = [
				{ key: "name", label: "Reference", nums: !0, hideOnMobile: !0 },
				{ key: "purpose", label: "Purpose", primary: !0 },
				{ key: "posting_date", label: "Requested", nums: !0, muted: !0 },
				{ key: "advance_amount", label: "Amount", align: "right", nums: !0 },
				{
					key: "outstanding",
					label: "Outstanding",
					align: "right",
					nums: !0,
					hideOnMobile: !0,
				},
				{ key: "status", label: "Status", align: "right", badge: !0 },
			],
			g = q(),
			i = A(!1),
			d = f(() => l.data),
			b = f(() => {
				var a;
				const t = ((a = d.value) == null ? void 0 : a.stats) || {};
				return [
					{
						label: "Outstanding",
						value: u(t.outstanding, { compact: !0 }),
						hint: "still to repay",
					},
					{
						label: "Repaid",
						value: u(t.repaid, { compact: !0 }),
						pct: t.pct_repaid,
						hint: `${t.pct_repaid || 0} percent of ${u(t.total, { compact: !0 })}`,
					},
					{ label: "Taken", value: u(t.total, { compact: !0 }), hint: "lifetime" },
				];
			});
		function y(t) {
			return t.docstatus !== 1
				? 0
				: (t.paid_amount || 0) - (t.claimed_amount || 0) - (t.return_amount || 0);
		}
		function k(t) {
			g.push(B("advance", t.name));
		}
		return (
			$(() => l.fetch()),
			(t, a) => (
				c(),
				p(
					_,
					null,
					[
						n(
							M,
							{ loading: o(l).loading && !o(l).data },
							{
								default: s(() => [
									n(
										x,
										{
											title: "Advances",
											subtitle: "Salary and travel advances",
										},
										{
											actions: s(() => [
												n(
													o(h),
													{
														variant: "solid",
														onClick:
															a[0] || (a[0] = (e) => (i.value = !0)),
													},
													{
														default: s(() => [
															...(a[3] ||
																(a[3] = [
																	r("Request Advance", -1),
																])),
														]),
														_: 1,
													},
												),
											]),
											_: 1,
										},
									),
									d.value
										? (c(),
										  p(
												_,
												{ key: 0 },
												[
													n(O, { tiles: b.value }, null, 8, ["tiles"]),
													n(
														C,
														{ title: "My Advances", padded: !1 },
														{
															default: s(() => [
																n(
																	N,
																	{
																		columns: v,
																		rows: d.value.advances,
																		clickable: "",
																		"empty-message":
																			"You have not requested an advance.",
																		onRowClick: k,
																	},
																	{
																		"cell-posting_date": s(
																			({ row: e }) => [
																				r(
																					m(
																						o(D)(
																							e.posting_date,
																						),
																					),
																					1,
																				),
																			],
																		),
																		"cell-advance_amount": s(
																			({ row: e }) => [
																				r(
																					m(
																						o(u)(
																							e.advance_amount,
																						),
																					),
																					1,
																				),
																			],
																		),
																		"cell-outstanding": s(
																			({ row: e }) => [
																				r(
																					m(o(u)(y(e))),
																					1,
																				),
																			],
																		),
																		"cell-status": s(
																			({ row: e }) => [
																				n(
																					S,
																					{
																						status:
																							e.docstatus ===
																							0
																								? "Draft"
																								: e.status,
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
												],
												64,
										  ))
										: R("", !0),
								]),
								_: 1,
							},
							8,
							["loading"],
						),
						n(
							w,
							{
								open: i.value,
								"onUpdate:open": a[1] || (a[1] = (e) => (i.value = e)),
								type: "advance",
								onSaved: a[2] || (a[2] = (e) => o(l).fetch()),
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
export { H as default };
