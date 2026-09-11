var C = Object.defineProperty;
var k = Object.getOwnPropertySymbols;
var $ = Object.prototype.hasOwnProperty,
	v = Object.prototype.propertyIsEnumerable;
var h = (r, a, t) =>
		a in r
			? C(r, a, { enumerable: !0, configurable: !0, writable: !0, value: t })
			: (r[a] = t),
	b = (r, a) => {
		for (var t in a || (a = {})) $.call(a, t) && h(r, t, a[t]);
		if (k) for (var t of k(a)) v.call(a, t) && h(r, t, a[t]);
		return r;
	};
import {
	L as w,
	o as l,
	d as m,
	w as o,
	f as _,
	g as c,
	X as N,
	e as d,
	t as x,
	Q as M,
	n as R,
	z as B,
	a as y,
	q as L,
} from "./frappe-ui-rHlwnvVy.js";
import { a as V, _ as z, b as D } from "./SectionCard-0tgyDAFI.js";
import { _ as O } from "./EmptyState-0_BFjfJU.js";
import { r as u } from "./index-6wvshjQq.js";
const S = { class: "shrink-0 text-base text-ink-gray-8" },
	q = { class: "truncate text-sm text-ink-gray-5" },
	E = {
		__name: "OrgChart",
		setup(r) {
			const a = y(() => u.data);
			function t(e, s = {}) {
				return b(
					{
						name: e.name,
						label: e.employee_name,
						role: e.designation || "—",
						image: e.image,
						children: [],
					},
					s,
				);
			}
			const p = y(() => {
				var f;
				const e = a.value;
				if (!(e != null && e.me)) return null;
				const s = t(e.me, { isMe: !0, children: (e.reports || []).map((i) => t(i)) }),
					g =
						(f = e.peers) != null && f.length
							? e.peers.map((i) => (i.name === e.me.name ? s : t(i)))
							: [s];
				if (!e.manager) return s;
				const n = t(e.manager, { children: g });
				return e.skip ? t(e.skip, { children: [n] }) : n;
			});
			return (
				w(() => u.fetch()),
				(e, s) => {
					const g = L("RouterLink");
					return (
						l(),
						m(
							D,
							{ loading: c(u).loading && !c(u).data },
							{
								default: o(() => [
									_(V, {
										title: "Org Chart",
										subtitle: "Your reporting line and team",
									}),
									a.value
										? (l(),
										  m(
												z,
												{ key: 0, title: "Reporting Structure" },
												{
													default: o(() => [
														p.value
															? (l(),
															  m(
																	c(N),
																	{
																		key: 0,
																		nodes: [p.value],
																		"node-key": "name",
																		guides: "connectors",
																	},
																	{
																		"item-prefix": o(
																			({ node: n }) => [
																				_(
																					c(R),
																					{
																						label: n.label,
																						image: n.image,
																						size: "lg",
																					},
																					null,
																					8,
																					[
																						"label",
																						"image",
																					],
																				),
																			],
																		),
																		"item-label": o(
																			({ node: n }) => [
																				_(
																					g,
																					{
																						to: n.isMe
																							? "/me"
																							: `/directory/${n.name}`,
																						class: "flex min-w-0 items-baseline gap-1.5",
																						onClick:
																							s[0] ||
																							(s[0] =
																								M(() => {}, [
																									"stop",
																								])),
																					},
																					{
																						default: o(
																							() => [
																								d(
																									"span",
																									S,
																									x(
																										n.label,
																									),
																									1,
																								),
																								s[1] ||
																									(s[1] =
																										d(
																											"span",
																											{
																												class: "shrink-0 font-bold text-ink-gray-4",
																											},
																											"·",
																											-1,
																										)),
																								d(
																									"span",
																									q,
																									x(
																										n.role,
																									),
																									1,
																								),
																							],
																						),
																						_: 2,
																					},
																					1032,
																					["to"],
																				),
																			],
																		),
																		_: 1,
																	},
																	8,
																	["nodes"],
															  ))
															: (l(),
															  m(O, {
																	key: 1,
																	message:
																		"No reporting structure to show.",
															  })),
													]),
													_: 1,
												},
										  ))
										: B("", !0),
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
	};
export { E as default };
