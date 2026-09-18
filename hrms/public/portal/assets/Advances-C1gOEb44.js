import {
	L as $,
	o as c,
	i as p,
	f as n,
	w as s,
	h as o,
	I as h,
	l as r,
	F as _,
	t as m,
	z as R,
	B as A,
	a as f,
	b as q,
} from "./frappe-ui-CXkWuvNK.js";
import { a as x, _ as C, b as M } from "./SectionCard-BKeIA1B1.js";
import { _ as N } from "./DataTable-KquPBl5L.js";
import { _ as O } from "./StatTiles-knaJnTjR.js";
import { _ as S } from "./StatusBadge-DcMGXIA6.js";
import { _ as w, r as B } from "./RequestDialog-DuFWjain.js";
import { j as u, b as l, d as D } from "./index-BpEXs0_U.js";
import "./EmptyState-DhAxAin0.js";
import "./RequestField-B8HqhQXt.js";
import "./DateField-BLUeL_2-.js";
import "./toast-Ca-cKV9o.js";
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
			d = f(() => u.data),
			b = f(() => {
				var a;
				const t = ((a = d.value) == null ? void 0 : a.stats) || {};
				return [
					{
						label: "Outstanding",
						value: l(t.outstanding, { compact: !0 }),
						hint: "still to repay",
					},
					{
						label: "Repaid",
						value: l(t.repaid, { compact: !0 }),
						pct: t.pct_repaid,
						hint: `${t.pct_repaid || 0} percent of ${l(t.total, { compact: !0 })}`,
					},
					{ label: "Taken", value: l(t.total, { compact: !0 }), hint: "lifetime" },
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
			$(() => u.fetch()),
			(t, a) => (
				c(),
				p(
					_,
					null,
					[
						n(
							M,
							{ loading: o(u).loading && !o(u).data },
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
																						o(l)(
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
																					m(o(l)(y(e))),
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
								onSaved: a[2] || (a[2] = (e) => o(u).fetch()),
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
