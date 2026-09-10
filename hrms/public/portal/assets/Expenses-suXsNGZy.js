import {
	L as F,
	o as u,
	h as m,
	f as l,
	w as i,
	g as n,
	I as k,
	k as v,
	F as _,
	t as r,
	d as h,
	e as s,
	i as w,
	z as y,
	B as M,
	a as $,
	b as R,
} from "./frappe-ui-D0k6koYp.js";
import { a as Y, _ as f, b as j } from "./SectionCard-C5Qs8pBJ.js";
import { _ as D } from "./DataTable-BPI_hH2T.js";
import { _ as L } from "./StatTiles-CcQndbp7.js";
import { _ as C } from "./StatusBadge-sSVuNJEI.js";
import { _ as P } from "./TotalRow-DhNOuPhk.js";
import { _ as q, r as z } from "./RequestDialog-UMsP4D4j.js";
import { g as p, d as N, a as d } from "./index-BSaIzYPn.js";
import "./EmptyState-38_uLDf3.js";
import "./RequestField-CEA0aLLd.js";
import "./DateField-DafgtgxX.js";
import "./toast-BPVivXt-.js";
const I = { class: "min-w-0" },
	O = { class: "truncate text-p-base text-ink-gray-8" },
	T = { class: "truncate text-base text-ink-gray-5" },
	U = { class: "shrink-0 text-right" },
	W = { class: "nums text-p-base text-ink-gray-9" },
	G = { class: "nums text-base text-ink-gray-5" },
	H = { class: "min-w-0" },
	J = { class: "truncate text-p-base text-ink-gray-8" },
	K = { class: "nums truncate text-base text-ink-gray-5" },
	Q = { class: "nums shrink-0 text-p-base text-ink-gray-9" },
	me = {
		__name: "Expenses",
		setup(X) {
			const S = [
					{ key: "name", label: "Claim", nums: !0, hideOnMobile: !0 },
					{ key: "purpose", label: "Purpose", primary: !0 },
					{ key: "posting_date", label: "Submitted", nums: !0, muted: !0 },
					{ key: "total_claimed_amount", label: "Amount", align: "right", nums: !0 },
					{ key: "display_status", label: "Status", align: "right", badge: !0 },
				],
				A = R(),
				o = $(() => p.data),
				g = M(!1),
				B = $(() => {
					var a;
					const t = ((a = o.value) == null ? void 0 : a.stats) || {};
					return [
						{
							label: "Claimed",
							value: d(t.claimed, { compact: !0 }),
							hint: `${t.count || 0} claims`,
						},
						{
							label: "Awaiting Approval",
							value: d(t.awaiting, { compact: !0 }),
							hint:
								t.oldest_age !== null && t.oldest_age !== void 0
									? `oldest ${t.oldest_age} days`
									: "nothing pending",
						},
						{
							label: "Reimbursed",
							value: d(t.reimbursed, { compact: !0 }),
							hint: "paid out",
						},
					];
				});
			function V(t) {
				return t == null ? "" : t === 0 ? "today" : t === 1 ? "1 day" : `${t} days`;
			}
			function E(t) {
				A.push(z("expense", t.name));
			}
			return (
				F(() => p.fetch()),
				(t, a) => {
					var b;
					return (
						u(),
						m(
							_,
							null,
							[
								l(
									j,
									{ loading: n(p).loading && !n(p).data },
									{
										default: i(() => {
											var c, x;
											return [
												l(
													Y,
													{
														title: "Expenses",
														subtitle: "Your claims and reimbursements",
													},
													{
														actions: i(() => [
															l(
																n(k),
																{
																	variant: "solid",
																	onClick:
																		a[0] ||
																		(a[0] = (e) =>
																			(g.value = !0)),
																},
																{
																	default: i(() => [
																		...(a[3] ||
																			(a[3] = [
																				v("New Claim", -1),
																			])),
																	]),
																	_: 1,
																},
															),
														]),
														_: 1,
													},
												),
												o.value
													? (u(),
													  m(
															_,
															{ key: 0 },
															[
																l(L, { tiles: B.value }, null, 8, [
																	"tiles",
																]),
																l(
																	f,
																	{
																		title: "My Claims",
																		padded: !1,
																	},
																	{
																		default: i(() => [
																			l(
																				D,
																				{
																					columns: S,
																					rows: o.value
																						.claims,
																					clickable: "",
																					"empty-message":
																						"You have not claimed any expenses yet.",
																					onRowClick: E,
																				},
																				{
																					"cell-total_claimed_amount":
																						i(
																							({
																								row: e,
																							}) => [
																								v(
																									r(
																										n(
																											d,
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
																						i(
																							({
																								row: e,
																							}) => [
																								v(
																									r(
																										e.posting_date
																											? n(
																													N,
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
																						i(
																							({
																								row: e,
																							}) => [
																								l(
																									C,
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
																(c = o.value.awaiting_claims) !=
																	null && c.length
																	? (u(),
																	  h(
																			f,
																			{
																				key: 0,
																				title: "With Your Approver",
																				padded: !1,
																			},
																			{
																				action: i(() => [
																					l(
																						C,
																						{
																							status: "pending",
																							label: `${o.value.awaiting_claims.length}`,
																						},
																						null,
																						8,
																						["label"],
																					),
																				]),
																				default: i(() => [
																					s("ul", null, [
																						(u(!0),
																						m(
																							_,
																							null,
																							w(
																								o
																									.value
																									.awaiting_claims,
																								(
																									e,
																								) => (
																									u(),
																									m(
																										"li",
																										{
																											key: e.name,
																											class: "flex items-center justify-between gap-3 border-b border-outline-gray-1 px-3.5 py-2.5 last:border-0",
																										},
																										[
																											s(
																												"div",
																												I,
																												[
																													s(
																														"div",
																														O,
																														r(
																															e.purpose ||
																																e.name,
																														),
																														1,
																													),
																													s(
																														"div",
																														T,
																														r(
																															e.approver_name ||
																																"No approver set",
																														),
																														1,
																													),
																												],
																											),
																											s(
																												"div",
																												U,
																												[
																													s(
																														"div",
																														W,
																														r(
																															n(
																																d,
																															)(
																																e.amount,
																																{
																																	currency:
																																		e.currency,
																																},
																															),
																														),
																														1,
																													),
																													s(
																														"div",
																														G,
																														r(
																															V(
																																e.days,
																															),
																														),
																														1,
																													),
																												],
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
																	: y("", !0),
																(x = o.value.advances) != null &&
																x.outstanding
																	? (u(),
																	  h(
																			f,
																			{
																				key: 1,
																				title: "Advance to Settle",
																				padded: !1,
																			},
																			{
																				action: i(() => [
																					l(n(k), {
																						variant:
																							"ghost",
																						route: "/advances",
																						label: "View all",
																					}),
																				]),
																				default: i(() => [
																					s("ul", null, [
																						(u(!0),
																						m(
																							_,
																							null,
																							w(
																								o
																									.value
																									.advances
																									.rows,
																								(
																									e,
																								) => (
																									u(),
																									m(
																										"li",
																										{
																											key: e.name,
																											class: "flex items-center justify-between gap-3 border-b border-outline-gray-1 px-3.5 py-2.5 last:border-0",
																										},
																										[
																											s(
																												"div",
																												H,
																												[
																													s(
																														"div",
																														J,
																														r(
																															e.purpose ||
																																e.name,
																														),
																														1,
																													),
																													s(
																														"div",
																														K,
																														r(
																															n(
																																d,
																															)(
																																e.paid_amount,
																															),
																														) +
																															" advanced on " +
																															r(
																																n(
																																	N,
																																)(
																																	e.posting_date,
																																),
																															),
																														1,
																													),
																												],
																											),
																											s(
																												"div",
																												Q,
																												r(
																													n(
																														d,
																													)(
																														e.outstanding,
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
																					]),
																					l(
																						P,
																						{
																							label: "Still to settle",
																							value: n(
																								d,
																							)(
																								o
																									.value
																									.advances
																									.outstanding,
																							),
																						},
																						null,
																						8,
																						["value"],
																					),
																					a[4] ||
																						(a[4] = s(
																							"p",
																							{
																								class: "px-3.5 pb-3.5 text-sm text-ink-gray-5",
																							},
																							" Claim against an advance and this settles automatically. ",
																							-1,
																						)),
																				]),
																				_: 1,
																			},
																	  ))
																	: y("", !0),
															],
															64,
													  ))
													: y("", !0),
											];
										}),
										_: 1,
									},
									8,
									["loading"],
								),
								l(
									q,
									{
										open: g.value,
										"onUpdate:open": a[1] || (a[1] = (c) => (g.value = c)),
										type: "expense",
										currency:
											(b = o.value) == null ? void 0 : b.claim_currency,
										onSaved: a[2] || (a[2] = (c) => n(p).fetch()),
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
export { me as default };
