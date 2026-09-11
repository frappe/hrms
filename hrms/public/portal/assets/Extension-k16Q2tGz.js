var I = Object.defineProperty;
var B = Object.getOwnPropertySymbols;
var J = Object.prototype.hasOwnProperty,
	K = Object.prototype.propertyIsEnumerable;
var L = (c, i, l) =>
		i in c
			? I(c, i, { enumerable: !0, configurable: !0, writable: !0, value: l })
			: (c[i] = l),
	j = (c, i) => {
		for (var l in i || (i = {})) J.call(i, l) && L(c, l, i[l]);
		if (B) for (var l of B(i)) K.call(i, l) && L(c, l, i[l]);
		return c;
	};
var E = (c, i, l) =>
	new Promise((f, b) => {
		var x = (y) => {
				try {
					w(l.next(y));
				} catch (k) {
					b(k);
				}
			},
			_ = (y) => {
				try {
					w(l.throw(y));
				} catch (k) {
					b(k);
				}
			},
			w = (y) => (y.done ? f(y.value) : Promise.resolve(y.value).then(x, _));
		w((l = l.apply(c, i)).next());
	});
import {
	c as M,
	v as P,
	o as a,
	d as n,
	w as g,
	h as r,
	f as F,
	R as X,
	F as v,
	i as C,
	g as $,
	I as R,
	a2 as q,
	e as p,
	z as m,
	t as h,
	s as N,
	u as G,
	a as H,
	r as T,
	B as Q,
} from "./frappe-ui-rHlwnvVy.js";
import { a as W, _ as V, b as Y } from "./SectionCard-0tgyDAFI.js";
import { _ as Z } from "./StatTiles-DcUJsMoQ.js";
import { _ as ee } from "./StatusBadge-ZWn2FvVw.js";
import { _ as ae } from "./DataTable-BY05XQx8.js";
import { _ as te } from "./FieldRow-C13lI4HG.js";
import { _ as le } from "./TotalRow-DkNHj82l.js";
import { _ as se } from "./EmptyState-0_BFjfJU.js";
import { _ as ne } from "./RequestField-DnRQOkWG.js";
import { n as ie, a as D, e as O } from "./toast-BxUFHbEO.js";
import "./DateField-c9rL8vfk.js";
const oe = { class: "flex flex-col" },
	re = { key: 0 },
	ue = { class: "min-w-0" },
	de = { class: "truncate text-p-base text-ink-gray-8" },
	ce = { class: "truncate text-base text-ink-gray-5" },
	me = { class: "flex shrink-0 items-center gap-2" },
	fe = { key: 1, class: "px-3.5 pb-3.5" },
	_e = { key: 0, class: "text-base text-ink-gray-5" },
	ye = { class: "grid gap-3 sm:grid-cols-2" },
	pe = ["onClick"],
	be = { class: "text-base-semibold text-ink-gray-9" },
	ge = { class: "text-base text-ink-gray-5" },
	ke = { key: 0, class: "text-base text-ink-gray-5" },
	ve = { class: "grid gap-3 sm:grid-cols-2" },
	Ue = {
		__name: "Extension",
		setup(c) {
			const i = G(),
				l = Q(""),
				f = T({}),
				b = T({}),
				x = M({ url: "hrms.api.portal_extensions.get_screen" }),
				_ = H(() => x.data);
			function w(u) {
				var d;
				for (const s of (u == null ? void 0 : u.sections) || [])
					if ((s.type === "choice" && (f[s.field] = s.current), s.type === "form"))
						for (const e of s.fields || [])
							b[e.fieldname] = (d = e.value) != null ? d : "";
			}
			function y() {
				x.fetch({ slug: i.params.slug }).then(w);
			}
			P(() => i.params.slug, y, { immediate: !0 });
			function k(u, d) {
				return E(this, null, function* () {
					l.value = u;
					try {
						const s = yield fetch(
							"/api/method/hrms.api.portal_extensions.run_action",
							{
								method: "POST",
								headers: {
									"Content-Type": "application/json",
									Accept: "application/json",
									"X-Frappe-CSRF-Token": window.csrf_token,
								},
								body: JSON.stringify({
									slug: i.params.slug,
									action: u,
									values: d || {},
								}),
							},
						);
						if (!s.ok) throw new Error(yield s.text());
						const e = (yield s.json()).message || {};
						e.file && S(e.file),
							e.spec && ((x.data = e.spec), w(e.spec)),
							ie(e.message || "Done");
					} catch (s) {
						D("Could not complete", O(s, "Try again in a moment."));
					} finally {
						l.value = "";
					}
				});
			}
			function z(u) {
				window.open(u, "_blank", "noopener");
			}
			function S(u) {
				return E(this, null, function* () {
					try {
						const d = yield fetch(u.url);
						if (!d.ok) throw new Error(yield d.text());
						const s = URL.createObjectURL(yield d.blob()),
							e = document.createElement("a");
						(e.href = s),
							(e.download = u.filename || `${u.label}.pdf`),
							e.click(),
							URL.revokeObjectURL(s);
					} catch (d) {
						D("Could not download", O(d, "Try again in a moment."));
					}
				});
			}
			return (u, d) => (
				a(),
				n(
					Y,
					{ loading: $(x).loading && !_.value },
					{
						default: g(() => {
							var s;
							return [
								_.value
									? (a(),
									  r(
											v,
											{ key: 0 },
											[
												F(
													W,
													{
														title: _.value.title,
														subtitle: _.value.subtitle,
													},
													X({ _: 2 }, [
														(s = _.value.actions) != null && s.length
															? {
																	name: "actions",
																	fn: g(() => [
																		(a(!0),
																		r(
																			v,
																			null,
																			C(
																				_.value.actions,
																				(e) => (
																					a(),
																					n(
																						$(R),
																						{
																							key: e.action,
																							variant:
																								e.variant ||
																								"subtle",
																							"icon-left":
																								e.icon,
																							label: e.label,
																							loading:
																								l.value ===
																								e.action,
																							disabled:
																								e.field
																									? f[
																											e
																												.field
																									  ] ===
																									  e.current
																									: !1,
																							onClick:
																								(
																									U,
																								) =>
																									k(
																										e.action,
																										j(
																											j(
																												{},
																												f,
																											),
																											b,
																										),
																									),
																						},
																						null,
																						8,
																						[
																							"variant",
																							"icon-left",
																							"label",
																							"loading",
																							"disabled",
																							"onClick",
																						],
																					)
																				),
																			),
																			128,
																		)),
																	]),
																	key: "0",
															  }
															: void 0,
													]),
													1032,
													["title", "subtitle"],
												),
												(a(!0),
												r(
													v,
													null,
													C(
														_.value.sections || [],
														(e, U) => (
															a(),
															n(
																q((e.width === "full", "div")),
																{ key: U },
																{
																	default: g(() => [
																		e.type === "stats"
																			? (a(),
																			  n(
																					Z,
																					{
																						key: 0,
																						tiles:
																							e.tiles ||
																							[],
																					},
																					null,
																					8,
																					["tiles"],
																			  ))
																			: e.type === "fields"
																			  ? (a(),
																			    n(
																						V,
																						{
																							key: 1,
																							title: e.title,
																							"readonly-label":
																								e.note,
																						},
																						{
																							default:
																								g(
																									() => [
																										p(
																											"dl",
																											oe,
																											[
																												(a(
																													!0,
																												),
																												r(
																													v,
																													null,
																													C(
																														e.rows ||
																															[],
																														(
																															t,
																														) => (
																															a(),
																															n(
																																te,
																																{
																																	key: t.label,
																																	label: t.label,
																																	value: t.value,
																																	locked: t.locked,
																																	nums: t.nums,
																																},
																																null,
																																8,
																																[
																																	"label",
																																	"value",
																																	"locked",
																																	"nums",
																																],
																															)
																														),
																													),
																													128,
																												)),
																											],
																										),
																									],
																								),
																							_: 2,
																						},
																						1032,
																						[
																							"title",
																							"readonly-label",
																						],
																			    ))
																			  : e.type === "table"
																			    ? (a(),
																			      n(
																							V,
																							{
																								key: 2,
																								title: e.title,
																								padded: !1,
																							},
																							{
																								default:
																									g(
																										() => [
																											F(
																												ae,
																												{
																													columns:
																														e.columns ||
																														[],
																													rows:
																														e.rows ||
																														[],
																													"id-key":
																														e.idKey ||
																														"name",
																													"empty-message":
																														e.empty ||
																														"Nothing here yet.",
																												},
																												null,
																												8,
																												[
																													"columns",
																													"rows",
																													"id-key",
																													"empty-message",
																												],
																											),
																											e.total
																												? (a(),
																												  n(
																														le,
																														{
																															key: 0,
																															label: e
																																.total
																																.label,
																															value: e
																																.total
																																.value,
																														},
																														null,
																														8,
																														[
																															"label",
																															"value",
																														],
																												  ))
																												: m(
																														"",
																														!0,
																												  ),
																										],
																									),
																								_: 2,
																							},
																							1032,
																							[
																								"title",
																							],
																			      ))
																			    : e.type ===
																			        "files"
																			      ? (a(),
																			        n(
																								V,
																								{
																									key: 3,
																									title: e.title,
																									padded: !1,
																								},
																								{
																									default:
																										g(
																											() => {
																												var t;
																												return [
																													(t =
																														e.files) !=
																														null &&
																													t.length
																														? (a(),
																														  r(
																																"ul",
																																re,
																																[
																																	(a(
																																		!0,
																																	),
																																	r(
																																		v,
																																		null,
																																		C(
																																			e.files,
																																			(
																																				o,
																																			) => (
																																				a(),
																																				r(
																																					"li",
																																					{
																																						key: o.label,
																																						class: "flex items-center justify-between gap-3 border-b border-outline-gray-1 px-3.5 py-2.5 last:border-0",
																																					},
																																					[
																																						p(
																																							"div",
																																							ue,
																																							[
																																								p(
																																									"div",
																																									de,
																																									h(
																																										o.label,
																																									),
																																									1,
																																								),
																																								p(
																																									"div",
																																									ce,
																																									h(
																																										o.hint,
																																									),
																																									1,
																																								),
																																							],
																																						),
																																						p(
																																							"div",
																																							me,
																																							[
																																								o.status
																																									? (a(),
																																									  n(
																																											ee,
																																											{
																																												key: 0,
																																												status: o.status,
																																											},
																																											null,
																																											8,
																																											[
																																												"status",
																																											],
																																									  ))
																																									: m(
																																											"",
																																											!0,
																																									  ),
																																								o.url
																																									? (a(),
																																									  n(
																																											$(
																																												R,
																																											),
																																											{
																																												key: 1,
																																												variant:
																																													"ghost",
																																												icon: "lucide-eye",
																																												label: `View ${o.label}`,
																																												onClick:
																																													(
																																														A,
																																													) =>
																																														z(
																																															o.url,
																																														),
																																											},
																																											null,
																																											8,
																																											[
																																												"label",
																																												"onClick",
																																											],
																																									  ))
																																									: m(
																																											"",
																																											!0,
																																									  ),
																																								o.url
																																									? (a(),
																																									  n(
																																											$(
																																												R,
																																											),
																																											{
																																												key: 2,
																																												variant:
																																													"ghost",
																																												icon: "lucide-download",
																																												label: `Download ${o.label}`,
																																												onClick:
																																													(
																																														A,
																																													) =>
																																														S(
																																															o,
																																														),
																																											},
																																											null,
																																											8,
																																											[
																																												"label",
																																												"onClick",
																																											],
																																									  ))
																																									: m(
																																											"",
																																											!0,
																																									  ),
																																							],
																																						),
																																					],
																																				)
																																			),
																																		),
																																		128,
																																	)),
																																],
																														  ))
																														: (a(),
																														  r(
																																"div",
																																fe,
																																[
																																	F(
																																		se,
																																		{
																																			message:
																																				e.empty ||
																																				"Nothing available yet.",
																																		},
																																		null,
																																		8,
																																		[
																																			"message",
																																		],
																																	),
																																],
																														  )),
																												];
																											},
																										),
																									_: 2,
																								},
																								1032,
																								[
																									"title",
																								],
																			        ))
																			      : e.type ===
																			          "note"
																			        ? (a(),
																			          r(
																									"div",
																									{
																										key: 4,
																										class: N(
																											[
																												"rounded-6 border px-3.5 py-2.5 text-p-base",
																												e.tone ===
																												"success"
																													? "border-outline-green-2 bg-surface-green-1 text-ink-green-3"
																													: "border-outline-gray-2 bg-surface-gray-1 text-ink-gray-7",
																											],
																										),
																									},
																									h(
																										e.text,
																									),
																									3,
																			          ))
																			        : e.type ===
																			            "choice"
																			          ? (a(),
																			            n(
																										V,
																										{
																											key: 5,
																											title: e.title,
																										},
																										{
																											default:
																												g(
																													() => [
																														e.hint
																															? (a(),
																															  r(
																																	"p",
																																	_e,
																																	h(
																																		e.hint,
																																	),
																																	1,
																															  ))
																															: m(
																																	"",
																																	!0,
																															  ),
																														p(
																															"div",
																															ye,
																															[
																																(a(
																																	!0,
																																),
																																r(
																																	v,
																																	null,
																																	C(
																																		e.options ||
																																			[],
																																		(
																																			t,
																																		) => (
																																			a(),
																																			r(
																																				"button",
																																				{
																																					key: t.value,
																																					type: "button",
																																					class: N(
																																						[
																																							"flex flex-col items-start gap-1 rounded-6 border p-3 text-left transition-colors",
																																							f[
																																								e
																																									.field
																																							] ===
																																							t.value
																																								? "border-outline-gray-4 bg-surface-gray-2"
																																								: "border-outline-gray-1 hover:bg-surface-gray-1",
																																						],
																																					),
																																					onClick:
																																						(
																																							o,
																																						) =>
																																							(f[
																																								e.field
																																							] =
																																								t.value),
																																				},
																																				[
																																					p(
																																						"span",
																																						be,
																																						h(
																																							t.label,
																																						),
																																						1,
																																					),
																																					p(
																																						"span",
																																						ge,
																																						h(
																																							t.hint,
																																						),
																																						1,
																																					),
																																				],
																																				10,
																																				pe,
																																			)
																																		),
																																	),
																																	128,
																																)),
																															],
																														),
																														e.action
																															? (a(),
																															  n(
																																	$(
																																		R,
																																	),
																																	{
																																		key: 1,
																																		class: "self-start",
																																		variant:
																																			e
																																				.action
																																				.variant ||
																																			"subtle",
																																		label: e
																																			.action
																																			.label,
																																		loading:
																																			l.value ===
																																			e
																																				.action
																																				.action,
																																		disabled:
																																			f[
																																				e
																																					.field
																																			] ===
																																			e.current,
																																		onClick:
																																			(
																																				t,
																																			) =>
																																				k(
																																					e
																																						.action
																																						.action,
																																					{
																																						[e.field]:
																																							f[
																																								e
																																									.field
																																							],
																																					},
																																				),
																																	},
																																	null,
																																	8,
																																	[
																																		"variant",
																																		"label",
																																		"loading",
																																		"disabled",
																																		"onClick",
																																	],
																															  ))
																															: m(
																																	"",
																																	!0,
																															  ),
																													],
																												),
																											_: 2,
																										},
																										1032,
																										[
																											"title",
																										],
																			            ))
																			          : e.type ===
																			              "form"
																			            ? (a(),
																			              n(
																											V,
																											{
																												key: 6,
																												title: e.title,
																											},
																											{
																												default:
																													g(
																														() => [
																															e.hint
																																? (a(),
																																  r(
																																		"p",
																																		ke,
																																		h(
																																			e.hint,
																																		),
																																		1,
																																  ))
																																: m(
																																		"",
																																		!0,
																																  ),
																															p(
																																"div",
																																ve,
																																[
																																	(a(
																																		!0,
																																	),
																																	r(
																																		v,
																																		null,
																																		C(
																																			e.fields ||
																																				[],
																																			(
																																				t,
																																			) => (
																																				a(),
																																				n(
																																					ne,
																																					{
																																						key: t.fieldname,
																																						modelValue:
																																							b[
																																								t
																																									.fieldname
																																							],
																																						"onUpdate:modelValue":
																																							(
																																								o,
																																							) =>
																																								(b[
																																									t.fieldname
																																								] =
																																									o),
																																						field: t,
																																						class: N(
																																							t.full &&
																																								"sm:col-span-2",
																																						),
																																					},
																																					null,
																																					8,
																																					[
																																						"modelValue",
																																						"onUpdate:modelValue",
																																						"field",
																																						"class",
																																					],
																																				)
																																			),
																																		),
																																		128,
																																	)),
																																],
																															),
																															e.action
																																? (a(),
																																  n(
																																		$(
																																			R,
																																		),
																																		{
																																			key: 1,
																																			class: "self-start",
																																			variant:
																																				e
																																					.action
																																					.variant ||
																																				"subtle",
																																			label: e
																																				.action
																																				.label,
																																			loading:
																																				l.value ===
																																				e
																																					.action
																																					.action,
																																			onClick:
																																				(
																																					t,
																																				) =>
																																					k(
																																						e
																																							.action
																																							.action,
																																						b,
																																					),
																																		},
																																		null,
																																		8,
																																		[
																																			"variant",
																																			"label",
																																			"loading",
																																			"onClick",
																																		],
																																  ))
																																: m(
																																		"",
																																		!0,
																																  ),
																														],
																													),
																												_: 2,
																											},
																											1032,
																											[
																												"title",
																											],
																			              ))
																			            : m(
																											"",
																											!0,
																			              ),
																	]),
																	_: 2,
																},
																1024,
															)
														),
													),
													128,
												)),
											],
											64,
									  ))
									: m("", !0),
							];
						}),
						_: 1,
					},
					8,
					["loading"],
				)
			);
		},
	};
export { Ue as default };
