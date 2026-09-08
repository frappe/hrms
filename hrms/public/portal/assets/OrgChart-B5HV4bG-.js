var M = Object.defineProperty;
var x = Object.getOwnPropertySymbols;
var N = Object.prototype.hasOwnProperty,
	B = Object.prototype.propertyIsEnumerable;
var b = (o, t, s) =>
		t in o
			? M(o, t, { enumerable: !0, configurable: !0, writable: !0, value: s })
			: (o[t] = s),
	y = (o, t) => {
		for (var s in t || (t = {})) N.call(t, s) && b(o, s, t[s]);
		if (x) for (var s of x(t)) B.call(t, s) && b(o, s, t[s]);
		return o;
	};
import {
	$ as O,
	P as R,
	q as L,
	o as r,
	f as p,
	g as m,
	h as l,
	s as g,
	F as v,
	i as _,
	a0 as S,
	S as V,
	v as z,
	j as D,
	k as c,
	x as C,
	t as F,
	C as H,
	a as $,
} from "./frappe-ui-BQ9PgXrr.js";
import { _ as w, a as I } from "./SectionCard-u_7VCKnT.js";
import { _ as j } from "./PageHead-3jtDpZ9g.js";
import { _ as q } from "./FieldRow-DbBPtAxY.js";
import { _ as E } from "./EmptyState-DNwecFw5.js";
import { o as d } from "./index-DKSqIuAQ.js";
const G = { key: 0, class: "org-tree" },
	P = { class: "flex min-w-0 items-baseline gap-1.5" },
	W = { class: "shrink-0 text-base text-ink-gray-8" },
	Y = { class: "truncate text-sm text-ink-gray-5" },
	A = { class: "flex flex-col" },
	J = {
		__name: "OrgChart",
		setup(o) {
			const t = $(() => d.data),
				s = {
					rowHeight: "48px",
					indentWidth: "28px",
					showIndentationGuides: !1,
					defaultCollapsed: !1,
				};
			function i(e, n = {}) {
				return y(
					{
						name: e.name,
						label: e.employee_name,
						role: e.designation || "—",
						image: e.image,
						children: [],
					},
					n,
				);
			}
			const h = $(() => {
				var k;
				const e = t.value;
				if (!(e != null && e.me)) return null;
				const n = i(e.me, { isMe: !0, children: (e.reports || []).map((u) => i(u)) }),
					f =
						(k = e.peers) != null && k.length
							? e.peers.map((u) => (u.name === e.me.name ? n : i(u)))
							: [n];
				if (!e.manager) return n;
				const a = i(e.manager, { children: f });
				return e.skip ? i(e.skip, { children: [a] }) : a;
			});
			return (
				R(() => d.fetch()),
				(e, n) => {
					const f = L("RouterLink");
					return (
						r(),
						p(
							I,
							{ loading: _(d).loading && !_(d).data },
							{
								default: m(() => [
									l(j, {
										title: "Org Chart",
										subtitle: "Your reporting line and team",
									}),
									t.value
										? (r(),
										  g(
												v,
												{ key: 0 },
												[
													l(
														w,
														{ title: "Reporting Structure" },
														{
															default: m(() => [
																h.value
																	? (r(),
																	  g("div", G, [
																			l(
																				_(S),
																				{
																					node: h.value,
																					"node-key":
																						"name",
																					options: s,
																				},
																				{
																					label: m(
																						({
																							node: a,
																						}) => [
																							l(
																								f,
																								{
																									to: a.isMe
																										? "/me"
																										: `/directory/${a.name}`,
																									class: z(
																										[
																											"-ml-1 flex min-w-0 items-center gap-2.5 rounded-md px-2 py-1.5 transition-colors hover:bg-surface-gray-2",
																											a.isMe &&
																												"bg-surface-gray-3",
																										],
																									),
																									onClick:
																										n[0] ||
																										(n[0] =
																											V(() => {}, [
																												"stop",
																											])),
																								},
																								{
																									default:
																										m(
																											() => [
																												l(
																													_(
																														D,
																													),
																													{
																														label: a.label,
																														image: a.image,
																														size: "xl",
																													},
																													null,
																													8,
																													[
																														"label",
																														"image",
																													],
																												),
																												c(
																													"div",
																													P,
																													[
																														c(
																															"span",
																															W,
																															C(
																																a.label,
																															),
																															1,
																														),
																														n[1] ||
																															(n[1] =
																																c(
																																	"span",
																																	{
																																		class: "shrink-0 font-bold text-ink-gray-4",
																																	},
																																	"·",
																																	-1,
																																)),
																														c(
																															"span",
																															Y,
																															C(
																																a.role,
																															),
																															1,
																														),
																													],
																												),
																											],
																										),
																									_: 2,
																								},
																								1032,
																								[
																									"to",
																									"class",
																								],
																							),
																						],
																					),
																					_: 1,
																				},
																				8,
																				["node"],
																			),
																	  ]))
																	: (r(),
																	  p(E, {
																			key: 1,
																			message:
																				"No reporting structure to show.",
																	  })),
															]),
															_: 1,
														},
													),
													l(
														w,
														{ title: "Headcount" },
														{
															default: m(() => [
																c("dl", A, [
																	(r(!0),
																	g(
																		v,
																		null,
																		F(
																			t.value.departments,
																			(a) => (
																				r(),
																				p(
																					q,
																					{
																						key: a.name,
																						label: a.name,
																						value: `${
																							a.count
																						} ${
																							a.count ===
																							1
																								? "person"
																								: "people"
																						}`,
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
													),
												],
												64,
										  ))
										: H("", !0),
								]),
								_: 1,
							},
							8,
							["loading"],
						)
					);
				}
			);
		},
	},
	ae = O(J, [["__scopeId", "data-v-83c2f619"]]);
export { ae as default };
