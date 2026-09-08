import {
	b as $,
	P as h,
	o as c,
	s as p,
	h as n,
	g as s,
	i as o,
	M as R,
	B as r,
	F as _,
	x as m,
	C as x,
	e as A,
	a as f,
} from "./frappe-ui-BQ9PgXrr.js";
import { _ as C, a as M } from "./SectionCard-u_7VCKnT.js";
import { _ as q } from "./PageHead-3jtDpZ9g.js";
import { _ as N } from "./DataTable-vZ6Z-J3d.js";
import { _ as O } from "./StatTiles-YoNxs_Qn.js";
import { _ as S } from "./StatusBadge-Bqz4zlkD.js";
import { _ as B, r as D } from "./RequestDialog-TPB8mqrQ.js";
import { j as l, b as u, d as P } from "./index-DKSqIuAQ.js";
import "./EmptyState-DNwecFw5.js";
import "./toast-9qekBDJT.js";
const I = {
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
			g = $(),
			i = A(!1),
			d = f(() => l.data),
			b = f(() => {
				var a;
				const e = ((a = d.value) == null ? void 0 : a.stats) || {};
				return [
					{
						label: "Outstanding",
						value: u(e.outstanding, { compact: !0 }),
						hint: "still to repay",
					},
					{
						label: "Repaid",
						value: u(e.repaid, { compact: !0 }),
						pct: e.pct_repaid,
						hint: `${e.pct_repaid || 0} percent of ${u(e.total, { compact: !0 })}`,
					},
					{ label: "Taken", value: u(e.total, { compact: !0 }), hint: "lifetime" },
				];
			});
		function y(e) {
			return e.docstatus !== 1
				? 0
				: (e.paid_amount || 0) - (e.claimed_amount || 0) - (e.return_amount || 0);
		}
		function k(e) {
			g.push(D("advance", e.name));
		}
		return (
			h(() => l.fetch()),
			(e, a) => (
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
										q,
										{
											title: "Advances",
											subtitle: "Salary and travel advances",
										},
										{
											actions: s(() => [
												n(
													o(R),
													{
														variant: "solid",
														onClick:
															a[0] || (a[0] = (t) => (i.value = !0)),
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
																			({ row: t }) => [
																				r(
																					m(
																						o(P)(
																							t.posting_date,
																						),
																					),
																					1,
																				),
																			],
																		),
																		"cell-advance_amount": s(
																			({ row: t }) => [
																				r(
																					m(
																						o(u)(
																							t.advance_amount,
																						),
																					),
																					1,
																				),
																			],
																		),
																		"cell-outstanding": s(
																			({ row: t }) => [
																				r(
																					m(o(u)(y(t))),
																					1,
																				),
																			],
																		),
																		"cell-status": s(
																			({ row: t }) => [
																				n(
																					S,
																					{
																						status:
																							t.docstatus ===
																							0
																								? "Draft"
																								: t.status,
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
										: x("", !0),
								]),
								_: 1,
							},
							8,
							["loading"],
						),
						n(
							B,
							{
								open: i.value,
								"onUpdate:open": a[1] || (a[1] = (t) => (i.value = t)),
								type: "advance",
								onSaved: a[2] || (a[2] = (t) => o(l).fetch()),
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
export { I as default };
