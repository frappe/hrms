var oe = Object.defineProperty,
	ue = Object.defineProperties;
var de = Object.getOwnPropertyDescriptors;
var X = Object.getOwnPropertySymbols;
var ce = Object.prototype.hasOwnProperty,
	fe = Object.prototype.propertyIsEnumerable;
var Y = (o, u, s) =>
		u in o
			? oe(o, u, { enumerable: !0, configurable: !0, writable: !0, value: s })
			: (o[u] = s),
	K = (o, u) => {
		for (var s in u || (u = {})) ce.call(u, s) && Y(o, s, u[s]);
		if (X) for (var s of X(u)) fe.call(u, s) && Y(o, s, u[s]);
		return o;
	},
	G = (o, u) => ue(o, de(u));
var z = (o, u, s) =>
	new Promise((N, m) => {
		var f = (p) => {
				try {
					q(s.next(p));
				} catch ($) {
					m($);
				}
			},
			b = (p) => {
				try {
					q(s.throw(p));
				} catch ($) {
					m($);
				}
			},
			q = (p) => (p.done ? N(p.value) : Promise.resolve(p.value).then(f, b));
		q((s = s.apply(o, u)).next());
	});
import { _ as H } from "./RequestField-CEA0aLLd.js";
import {
	c as F,
	v as me,
	o as r,
	d as Q,
	w as v,
	e as n,
	h as d,
	t as g,
	g as y,
	z as k,
	f as h,
	I as _,
	k as B,
	y as pe,
	F as C,
	i as R,
	s as W,
	U as ve,
	B as S,
	a as w,
	r as ge,
} from "./frappe-ui-D0k6koYp.js";
import { a as ye } from "./index-BSaIzYPn.js";
import { a as M, n as Z, e as be } from "./toast-BPVivXt-.js";
const V = (o) => `hrms.api.employee_requests.${o}`,
	xe = F({ url: V("get_form") }),
	Je = F({ url: V("get_request") }),
	he = F({ url: V("create_request") }),
	ke = F({ url: V("update_request") }),
	Pe = F({ url: V("delete_request") });
function Xe(o, u) {
	return `/requests/${o}/${u}`;
}
const _e = { key: 0, class: "flex items-center gap-2 py-6 text-base text-ink-gray-5" },
	we = { key: 1, class: "flex flex-col gap-4" },
	qe = { key: 0, class: "grid gap-3 sm:grid-cols-2" },
	$e = { class: "flex items-center justify-between" },
	Ce = { class: "text-base-medium text-ink-gray-5" },
	Se = { class: "grid gap-3 sm:grid-cols-3" },
	Be = { key: 2, class: "flex flex-col gap-2 border-t border-outline-gray-1 pt-3" },
	Re = { key: 0, class: "flex flex-col gap-1.5" },
	Fe = ["href"],
	Ve = { class: "truncate" },
	Ne = { key: 1, class: "flex flex-col gap-1.5" },
	je = { class: "flex min-w-0 items-center gap-2" },
	Me = { class: "truncate text-p-base text-ink-gray-8" },
	Ae = { class: "nums shrink-0 text-base text-ink-gray-5" },
	Ee = { class: "flex items-center justify-between gap-3" },
	Oe = { key: 0, class: "nums text-p-base text-ink-gray-7" },
	Ue = { class: "ml-auto flex gap-2" },
	I = 5,
	L = 10,
	Ye = {
		__name: "RequestDialog",
		props: {
			open: Boolean,
			type: { type: String, required: !0 },
			request: { type: Object, default: null },
			currency: { type: String, default: null },
		},
		emits: ["update:open", "saved"],
		setup(o, { emit: u }) {
			const s = o,
				N = u,
				m = S(null),
				f = ge({}),
				b = S([]),
				q = S([]),
				p = S([]),
				$ = S(null),
				A = S(!1),
				E = w(() => {
					var t;
					return !!((t = s.request) != null && t.name);
				}),
				O = w({ get: () => s.open, set: (t) => N("update:open", t) }),
				ee = w(() => {
					var e;
					const t = ((e = m.value) == null ? void 0 : e.label) || "Request";
					return E.value ? `Edit ${t}` : `New ${t}`;
				}),
				j = w(() => {
					var t;
					return (((t = m.value) == null ? void 0 : t.fields) || []).filter(
						(e) => e.type !== "table",
					);
				}),
				c = w(() => {
					var t;
					return (((t = m.value) == null ? void 0 : t.fields) || []).find(
						(e) => e.type === "table",
					);
				}),
				U = w(() => q.value.filter((t) => !p.value.includes(t.name))),
				D = w(() => {
					const t = c.value;
					if (!t) return null;
					const e = t.fields.find((a) => a.type === "number");
					return e
						? (f[t.fieldname] || []).reduce(
								(a, l) => a + (Number(l[e.fieldname]) || 0),
								0,
						  )
						: null;
				});
			function T() {
				return Object.fromEntries(
					c.value.fields.map((t) => [t.fieldname, t.type === "checkbox" ? !1 : ""]),
				);
			}
			function te() {
				f[c.value.fieldname].push(T());
			}
			function ae() {
				var e, a;
				const t = ((e = s.request) == null ? void 0 : e.values) || {};
				for (const l of Object.keys(f)) delete f[l];
				for (const l of j.value) {
					const i = t[l.fieldname];
					f[l.fieldname] = l.type === "checkbox" ? !!i : i != null ? i : "";
				}
				if (c.value) {
					const l = t[c.value.fieldname];
					f[c.value.fieldname] =
						l != null && l.length
							? l.map((i) =>
									Object.fromEntries(
										c.value.fields.map((x) => {
											var P;
											return [
												x.fieldname,
												(P = i[x.fieldname]) != null ? P : "",
											];
										}),
									),
							  )
							: [T()];
				}
				(q.value = ((a = s.request) == null ? void 0 : a.attachments) || []),
					(b.value = []),
					(p.value = []);
			}
			me(
				() => [s.open, s.type],
				(e) =>
					z(this, [e], function* ([t]) {
						t && ((m.value = yield xe.fetch({ request_type: s.type })), ae());
					}),
				{ immediate: !0 },
			);
			function le(t) {
				return t >= 1024 * 1024
					? `${(t / (1024 * 1024)).toFixed(1)} MB`
					: `${Math.max(1, Math.round(t / 1024))} KB`;
			}
			function se(t) {
				for (const e of t.target.files) {
					if (U.value.length + b.value.length >= I) {
						M("Too many files", `You can attach at most ${I} files.`);
						break;
					}
					if (e.size > L * 1024 * 1024) {
						M("File too large", `${e.name} is over ${L} MB.`);
						continue;
					}
					b.value.push(e);
				}
				t.target.value = "";
			}
			function ne(t) {
				return new Promise((e, a) => {
					const l = new FileReader();
					(l.onload = () => e(String(l.result).split(",")[1])),
						(l.onerror = () => a(new Error(`Could not read ${t.name}`))),
						l.readAsDataURL(t);
				});
			}
			function J() {
				O.value = !1;
			}
			function re() {
				var e;
				for (const a of j.value)
					if (a.required && !String((e = f[a.fieldname]) != null ? e : "").trim())
						return `${a.label} is required`;
				const t = c.value;
				if (t)
					for (const [a, l] of (f[t.fieldname] || []).entries())
						for (const i of t.fields) {
							if (!i.required) continue;
							const x = l[i.fieldname];
							if (
								i.type === "number"
									? !(Number(x) > 0)
									: !String(x != null ? x : "").trim()
							)
								return `${i.label} is required for ${t.row_label.toLowerCase()} ${
									a + 1
								}`;
						}
				return null;
			}
			function ie() {
				return z(this, null, function* () {
					const t = re();
					if (t) {
						M("Incomplete form", t);
						return;
					}
					A.value = !0;
					try {
						const e = [];
						for (const l of b.value)
							e.push({ filename: l.name, content: yield ne(l) });
						const a = {
							request_type: s.type,
							values: JSON.stringify(f),
							attachments: JSON.stringify(e),
						};
						E.value
							? (yield ke.submit(
									G(K({}, a), {
										name: s.request.name,
										removed_attachments: JSON.stringify(p.value),
									}),
							  ),
							  Z(`${m.value.label} updated`))
							: (yield he.submit(a),
							  Z(`${m.value.label} saved`, "It is now with your approver.")),
							N("saved"),
							J();
					} catch (e) {
						M("Could not save", be(e, "Try again in a moment."));
					} finally {
						A.value = !1;
					}
				});
			}
			return (t, e) => (
				r(),
				Q(
					y(ve),
					{
						open: O.value,
						"onUpdate:open": e[1] || (e[1] = (a) => (O.value = a)),
						title: ee.value,
						size: c.value ? "lg" : "md",
					},
					{
						"body-content": v(() => [
							m.value
								? (r(),
								  d("div", we, [
										j.value.length
											? (r(),
											  d("div", qe, [
													(r(!0),
													d(
														C,
														null,
														R(
															j.value,
															(a) => (
																r(),
																d(
																	"div",
																	{
																		key: a.fieldname,
																		class: W(
																			a.full &&
																				"sm:col-span-2",
																		),
																	},
																	[
																		h(
																			H,
																			{
																				modelValue:
																					f[a.fieldname],
																				"onUpdate:modelValue":
																					(l) =>
																						(f[
																							a.fieldname
																						] = l),
																				field: a,
																			},
																			null,
																			8,
																			[
																				"modelValue",
																				"onUpdate:modelValue",
																				"field",
																			],
																		),
																	],
																	2,
																)
															),
														),
														128,
													)),
											  ]))
											: k("", !0),
										c.value
											? (r(),
											  d(
													C,
													{ key: 1 },
													[
														(r(!0),
														d(
															C,
															null,
															R(
																f[c.value.fieldname],
																(a, l) => (
																	r(),
																	d(
																		"div",
																		{
																			key: l,
																			class: "flex flex-col gap-3 rounded-6 border border-outline-gray-2 p-3",
																		},
																		[
																			n("div", $e, [
																				n(
																					"span",
																					Ce,
																					g(
																						c.value
																							.row_label,
																					) +
																						" " +
																						g(l + 1),
																					1,
																				),
																				f[
																					c.value
																						.fieldname
																				].length > 1
																					? (r(),
																					  Q(
																							y(_),
																							{
																								key: 0,
																								variant:
																									"ghost",
																								"aria-label": `Remove ${c.value.row_label.toLowerCase()}`,
																								onClick:
																									(
																										i,
																									) =>
																										f[
																											c
																												.value
																												.fieldname
																										].splice(
																											l,
																											1,
																										),
																							},
																							{
																								icon: v(
																									() => [
																										...(e[3] ||
																											(e[3] =
																												[
																													n(
																														"span",
																														{
																															class: "h-3.5 w-3.5 lucide-trash-2",
																															"aria-hidden":
																																"true",
																														},
																														null,
																														-1,
																													),
																												])),
																									],
																								),
																								_: 1,
																							},
																							8,
																							[
																								"aria-label",
																								"onClick",
																							],
																					  ))
																					: k("", !0),
																			]),
																			n("div", Se, [
																				(r(!0),
																				d(
																					C,
																					null,
																					R(
																						c.value
																							.fields,
																						(i) => (
																							r(),
																							d(
																								"div",
																								{
																									key: i.fieldname,
																									class: W(
																										i.full &&
																											"sm:col-span-3",
																									),
																								},
																								[
																									h(
																										H,
																										{
																											modelValue:
																												a[
																													i
																														.fieldname
																												],
																											"onUpdate:modelValue":
																												(
																													x,
																												) =>
																													(a[
																														i.fieldname
																													] =
																														x),
																											field: i,
																										},
																										null,
																										8,
																										[
																											"modelValue",
																											"onUpdate:modelValue",
																											"field",
																										],
																									),
																								],
																								2,
																							)
																						),
																					),
																					128,
																				)),
																			]),
																		],
																	)
																),
															),
															128,
														)),
														h(
															y(_),
															{
																variant: "subtle",
																class: "self-start",
																onClick: te,
															},
															{
																prefix: v(() => [
																	...(e[4] ||
																		(e[4] = [
																			n(
																				"span",
																				{
																					class: "h-3.5 w-3.5 lucide-plus",
																					"aria-hidden":
																						"true",
																				},
																				null,
																				-1,
																			),
																		])),
																]),
																default: v(() => [
																	B(
																		" Add Another " +
																			g(c.value.row_label),
																		1,
																	),
																]),
																_: 1,
															},
														),
													],
													64,
											  ))
											: k("", !0),
										m.value.supports_attachments
											? (r(),
											  d("div", Be, [
													e[11] ||
														(e[11] = n(
															"span",
															{
																class: "text-base-medium text-ink-gray-5",
															},
															"Attachments",
															-1,
														)),
													U.value.length
														? (r(),
														  d("ul", Re, [
																(r(!0),
																d(
																	C,
																	null,
																	R(
																		U.value,
																		(a) => (
																			r(),
																			d(
																				"li",
																				{
																					key: a.name,
																					class: "flex items-center justify-between gap-2 rounded-4 border border-outline-gray-2 px-2 py-1.5",
																				},
																				[
																					n(
																						"a",
																						{
																							href: a.file_url,
																							target: "_blank",
																							rel: "noopener",
																							class: "flex min-w-0 items-center gap-2 text-p-base text-ink-gray-8 hover:underline",
																						},
																						[
																							e[5] ||
																								(e[5] =
																									n(
																										"span",
																										{
																											class: "h-3.5 w-3.5 shrink-0 text-ink-gray-4 lucide-paperclip",
																											"aria-hidden":
																												"true",
																										},
																										null,
																										-1,
																									)),
																							n(
																								"span",
																								Ve,
																								g(
																									a.file_name,
																								),
																								1,
																							),
																						],
																						8,
																						Fe,
																					),
																					h(
																						y(_),
																						{
																							class: "shrink-0",
																							variant:
																								"ghost",
																							"aria-label":
																								"Remove attachment",
																							onClick:
																								(
																									l,
																								) =>
																									p.value.push(
																										a.name,
																									),
																						},
																						{
																							icon: v(
																								() => [
																									...(e[6] ||
																										(e[6] =
																											[
																												n(
																													"span",
																													{
																														class: "h-3.5 w-3.5 lucide-x",
																														"aria-hidden":
																															"true",
																													},
																													null,
																													-1,
																												),
																											])),
																								],
																							),
																							_: 1,
																						},
																						8,
																						[
																							"onClick",
																						],
																					),
																				],
																			)
																		),
																	),
																	128,
																)),
														  ]))
														: k("", !0),
													b.value.length
														? (r(),
														  d("ul", Ne, [
																(r(!0),
																d(
																	C,
																	null,
																	R(
																		b.value,
																		(a, l) => (
																			r(),
																			d(
																				"li",
																				{
																					key:
																						a.name + l,
																					class: "flex items-center justify-between gap-2 rounded-4 border border-outline-gray-2 px-2 py-1.5",
																				},
																				[
																					n("div", je, [
																						e[7] ||
																							(e[7] =
																								n(
																									"span",
																									{
																										class: "h-3.5 w-3.5 shrink-0 text-ink-gray-4 lucide-paperclip",
																										"aria-hidden":
																											"true",
																									},
																									null,
																									-1,
																								)),
																						n(
																							"span",
																							Me,
																							g(
																								a.name,
																							),
																							1,
																						),
																						n(
																							"span",
																							Ae,
																							g(
																								le(
																									a.size,
																								),
																							),
																							1,
																						),
																					]),
																					h(
																						y(_),
																						{
																							class: "shrink-0",
																							variant:
																								"ghost",
																							"aria-label":
																								"Remove attachment",
																							onClick:
																								(
																									i,
																								) =>
																									b.value.splice(
																										l,
																										1,
																									),
																						},
																						{
																							icon: v(
																								() => [
																									...(e[8] ||
																										(e[8] =
																											[
																												n(
																													"span",
																													{
																														class: "h-3.5 w-3.5 lucide-x",
																														"aria-hidden":
																															"true",
																													},
																													null,
																													-1,
																												),
																											])),
																								],
																							),
																							_: 1,
																						},
																						8,
																						[
																							"onClick",
																						],
																					),
																				],
																			)
																		),
																	),
																	128,
																)),
														  ]))
														: k("", !0),
													h(
														y(_),
														{
															variant: "subtle",
															class: "self-start",
															onClick:
																e[0] ||
																(e[0] = (a) => $.value.click()),
														},
														{
															prefix: v(() => [
																...(e[9] ||
																	(e[9] = [
																		n(
																			"span",
																			{
																				class: "h-3.5 w-3.5 lucide-paperclip",
																				"aria-hidden":
																					"true",
																			},
																			null,
																			-1,
																		),
																	])),
															]),
															default: v(() => [
																e[10] ||
																	(e[10] = B(
																		" Attach Files ",
																		-1,
																	)),
															]),
															_: 1,
														},
													),
													n(
														"input",
														{
															ref_key: "fileInput",
															ref: $,
															type: "file",
															multiple: "",
															class: "hidden",
															accept: "image/png,image/jpeg,image/gif,.pdf,.doc,.docx,.xls,.xlsx,.txt,.csv",
															onChange: se,
														},
														null,
														544,
													),
													n(
														"p",
														{ class: "text-base text-ink-gray-5" },
														" Up to " +
															g(I) +
															" files, " +
															g(L) +
															" MB each. ",
													),
											  ]))
											: k("", !0),
										e[12] ||
											(e[12] = n(
												"p",
												{ class: "text-base text-ink-gray-5" },
												" Saved as a draft. Your approver reviews and submits it. ",
												-1,
											)),
								  ]))
								: (r(),
								  d("div", _e, [
										h(y(pe), { class: "h-4 w-4" }),
										e[2] || (e[2] = B(" Loading ", -1)),
								  ])),
						]),
						actions: v(() => [
							n("div", Ee, [
								D.value !== null
									? (r(),
									  d(
											"span",
											Oe,
											" Total " +
												g(y(ye)(D.value, { currency: o.currency })),
											1,
									  ))
									: k("", !0),
								n("div", Ue, [
									h(
										y(_),
										{ variant: "subtle", onClick: J },
										{
											default: v(() => [
												...(e[13] || (e[13] = [B("Cancel", -1)])),
											]),
											_: 1,
										},
									),
									h(
										y(_),
										{
											variant: "solid",
											loading: A.value,
											disabled: !m.value,
											onClick: ie,
										},
										{
											default: v(() => [
												B(g(E.value ? "Save Changes" : "Save"), 1),
											]),
											_: 1,
										},
										8,
										["loading", "disabled"],
									),
								]),
							]),
						]),
						_: 1,
					},
					8,
					["open", "title", "size"],
				)
			);
		},
	};
export { Ye as _, Je as a, xe as b, Pe as d, Xe as r };
