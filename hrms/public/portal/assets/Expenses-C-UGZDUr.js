import {
	b as h,
	P as C,
	o,
	s as u,
	h as s,
	g as l,
	i,
	M as N,
	B as d,
	F as p,
	t as w,
	f,
	x as y,
	C as A,
	e as B,
	a as g,
} from "./frappe-ui-BQ9PgXrr.js";
import { _ as b, a as M } from "./SectionCard-u_7VCKnT.js";
import { _ as S } from "./PageHead-3jtDpZ9g.js";
import { _ as E } from "./DashGrid-Bd23iLvt.js";
import { _ as P } from "./DataTable-vZ6Z-J3d.js";
import { _ as R } from "./StatTiles-YoNxs_Qn.js";
import { _ as V } from "./StatusBadge-Bqz4zlkD.js";
import { _ as D } from "./FieldRow-DbBPtAxY.js";
import { _ as F } from "./EmptyState-DNwecFw5.js";
import { _ as T, r as Y } from "./RequestDialog-TPB8mqrQ.js";
import { g as r, d as q, b as m } from "./index-DKSqIuAQ.js";
import "./toast-9qekBDJT.js";
const L = { key: 0, class: "flex flex-col" },
	ee = {
		__name: "Expenses",
		setup(O) {
			const v = [
					{ key: "name", label: "Claim", nums: !0, hideOnMobile: !0 },
					{ key: "purpose", label: "Purpose", primary: !0 },
					{ key: "posting_date", label: "Submitted", nums: !0, muted: !0 },
					{ key: "total_claimed_amount", label: "Amount", align: "right", nums: !0 },
					{ key: "display_status", label: "Status", align: "right", badge: !0 },
				],
				k = h(),
				n = g(() => r.data),
				c = B(!1),
				$ = g(() => {
					var a;
					const t = ((a = n.value) == null ? void 0 : a.stats) || {};
					return [
						{
							label: "Claimed",
							value: m(t.claimed, { compact: !0 }),
							hint: `${t.count || 0} claims`,
						},
						{
							label: "Awaiting Approval",
							value: m(t.awaiting, { compact: !0 }),
							hint:
								t.oldest_age !== null && t.oldest_age !== void 0
									? `oldest ${t.oldest_age} days`
									: "nothing pending",
						},
						{
							label: "Reimbursed",
							value: m(t.reimbursed, { compact: !0 }),
							hint: "paid out",
						},
					];
				});
			function x(t) {
				k.push(Y("expense", t.name));
			}
			return (
				C(() => r.fetch()),
				(t, a) => {
					var _;
					return (
						o(),
						u(
							p,
							null,
							[
								s(
									M,
									{ loading: i(r).loading && !i(r).data },
									{
										default: l(() => [
											s(
												S,
												{
													title: "Expenses",
													subtitle: "Your claims and reimbursements",
												},
												{
													actions: l(() => [
														s(
															i(N),
															{
																variant: "solid",
																onClick:
																	a[0] ||
																	(a[0] = (e) => (c.value = !0)),
															},
															{
																default: l(() => [
																	...(a[3] ||
																		(a[3] = [
																			d("New Claim", -1),
																		])),
																]),
																_: 1,
															},
														),
													]),
													_: 1,
												},
											),
											n.value
												? (o(),
												  u(
														p,
														{ key: 0 },
														[
															s(R, { tiles: $.value }, null, 8, [
																"tiles",
															]),
															s(E, null, {
																main: l(() => [
																	s(
																		b,
																		{
																			title: "My Claims",
																			padded: !1,
																		},
																		{
																			default: l(() => [
																				s(
																					P,
																					{
																						columns: v,
																						rows: n
																							.value
																							.claims,
																						clickable:
																							"",
																						"empty-message":
																							"You have not claimed any expenses yet.",
																						onRowClick:
																							x,
																					},
																					{
																						"cell-total_claimed_amount":
																							l(
																								({
																									row: e,
																								}) => [
																									d(
																										y(
																											i(
																												m,
																											)(
																												e.total_claimed_amount,
																												{
																													currency:
																														e.currency,
																												},
																											),
																										),
																										1,
																									),
																								],
																							),
																						"cell-posting_date":
																							l(
																								({
																									row: e,
																								}) => [
																									d(
																										y(
																											e.posting_date
																												? i(
																														q,
																												  )(
																														e.posting_date,
																												  )
																												: "Not submitted",
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
																									s(
																										V,
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
																	s(
																		b,
																		{
																			title: "Claim Types",
																			"readonly-label":
																				"As per policy",
																		},
																		{
																			default: l(() => [
																				n.value.claim_types
																					.length
																					? (o(),
																					  u("dl", L, [
																							(o(!0),
																							u(
																								p,
																								null,
																								w(
																									n
																										.value
																										.claim_types,
																									(
																										e,
																									) => (
																										o(),
																										f(
																											D,
																											{
																												key: e.name,
																												label: e.name,
																												value:
																													e.description ||
																													"No description",
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
																					  ]))
																					: (o(),
																					  f(F, {
																							key: 1,
																							message:
																								"No expense claim types configured.",
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
												: A("", !0),
										]),
										_: 1,
									},
									8,
									["loading"],
								),
								s(
									T,
									{
										open: c.value,
										"onUpdate:open": a[1] || (a[1] = (e) => (c.value = e)),
										type: "expense",
										currency:
											(_ = n.value) == null ? void 0 : _.claim_currency,
										onSaved: a[2] || (a[2] = (e) => i(r).fetch()),
									},
									null,
									8,
									["open", "currency"],
								),
							],
							64,
						)
					);
				}
			);
		},
	};
export { ee as default };
