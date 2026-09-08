var ue = Object.defineProperty,
	de = Object.defineProperties;
var ce = Object.getOwnPropertyDescriptors;
var K = Object.getOwnPropertySymbols;
var me = Object.prototype.hasOwnProperty,
	fe = Object.prototype.propertyIsEnumerable;
var G = (a, o, n) =>
		o in a
			? ue(a, o, { enumerable: !0, configurable: !0, writable: !0, value: n })
			: (a[o] = n),
	H = (a, o) => {
		for (var n in o || (o = {})) me.call(o, n) && G(a, n, o[n]);
		if (K) for (var n of K(o)) fe.call(o, n) && G(a, n, o[n]);
		return a;
	},
	Q = (a, o) => de(a, ce(o));
var Y = (a, o, n) =>
	new Promise((w, m) => {
		var i = (g) => {
				try {
					V(n.next(g));
				} catch (C) {
					m(C);
				}
			},
			y = (g) => {
				try {
					V(n.throw(g));
				} catch (C) {
					m(C);
				}
			},
			V = (g) => (g.done ? w(g.value) : Promise.resolve(g.value).then(i, y));
		V((n = n.apply(a, o)).next());
	});
import {
	o as r,
	s as u,
	B as F,
	x as h,
	C as k,
	h as p,
	i as c,
	X as pe,
	f as A,
	N as ve,
	a as _,
	c as M,
	w as ye,
	g as b,
	k as v,
	M as q,
	A as ge,
	F as S,
	t as R,
	v as W,
	p as $,
	Y as be,
	e as B,
	r as he,
} from "./frappe-ui-BQ9PgXrr.js";
import { b as xe } from "./index-DKSqIuAQ.js";
import { a as U, n as Z, e as ke } from "./toast-9qekBDJT.js";
const _e = { class: "flex flex-col gap-1.5" },
	we = { key: 0, class: "block text-base text-ink-gray-5" },
	qe = { key: 0, class: "text-ink-red-3" },
	$e = {
		__name: "DateField",
		props: {
			modelValue: String,
			label: String,
			required: Boolean,
			placeholder: { type: String, default: "Select a date" },
		},
		emits: ["update:modelValue"],
		setup(a) {
			return (o, n) => (
				r(),
				u("div", _e, [
					a.label
						? (r(),
						  u("label", we, [
								F(h(a.label) + " ", 1),
								a.required ? (r(), u("span", qe, "*")) : k("", !0),
						  ]))
						: k("", !0),
					p(
						c(pe),
						{
							class: "w-full",
							"input-class": "w-full",
							"model-value": a.modelValue,
							placeholder: a.placeholder,
							format: "D MMM YYYY",
							"onUpdate:modelValue":
								n[0] || (n[0] = (w) => o.$emit("update:modelValue", w)),
						},
						null,
						8,
						["model-value", "placeholder"],
					),
				])
			);
		},
	},
	ee = {
		__name: "RequestField",
		props: {
			field: { type: Object, required: !0 },
			modelValue: { type: [String, Number, Boolean], default: "" },
		},
		emits: ["update:modelValue"],
		setup(a) {
			const o = a,
				n = _(
					() =>
						({
							number: "number",
							textarea: "textarea",
							select: "select",
							checkbox: "checkbox",
						})[o.field.type] || "text",
				),
				w = _(() => {
					if (o.field.type === "select")
						return [
							{ label: `Select a ${o.field.label.toLowerCase()}`, value: "" },
							...(o.field.options || []).map((m) => ({ label: m, value: m })),
						];
				});
			return (m, i) =>
				a.field.type === "date"
					? (r(),
					  A(
							$e,
							{
								key: 0,
								"model-value": a.modelValue,
								label: a.field.label,
								required: a.field.required,
								"onUpdate:modelValue":
									i[0] || (i[0] = (y) => m.$emit("update:modelValue", y)),
							},
							null,
							8,
							["model-value", "label", "required"],
					  ))
					: (r(),
					  A(
							c(ve),
							{
								key: 1,
								"model-value": a.modelValue,
								type: n.value,
								label: a.field.label,
								options: w.value,
								placeholder: a.field.placeholder,
								required: a.field.type === "checkbox" ? void 0 : a.field.required,
								"onUpdate:modelValue":
									i[1] || (i[1] = (y) => m.$emit("update:modelValue", y)),
							},
							null,
							8,
							["model-value", "type", "label", "options", "placeholder", "required"],
					  ));
		},
	},
	N = (a) => `hrms.api.employee_requests.${a}`,
	Ve = M({ url: N("get_form") }),
	He = M({ url: N("get_request") }),
	Ce = M({ url: N("create_request") }),
	Se = M({ url: N("update_request") }),
	Qe = M({ url: N("delete_request") });
function We(a, o) {
	return `/requests/${a}/${o}`;
}
const Be = { key: 0, class: "flex items-center gap-2 py-6 text-base text-ink-gray-5" },
	Fe = { key: 1, class: "flex flex-col gap-4" },
	Re = { key: 0, class: "grid gap-3 sm:grid-cols-2" },
	Me = { class: "flex items-center justify-between" },
	Ne = { class: "text-base font-medium text-ink-gray-5" },
	je = { class: "grid gap-3 sm:grid-cols-3" },
	Ue = { key: 2, class: "flex flex-col gap-2 border-t border-outline-gray-1 pt-3" },
	Ae = { key: 0, class: "flex flex-col gap-1.5" },
	Oe = ["href"],
	Ee = { class: "truncate" },
	Le = { key: 1, class: "flex flex-col gap-1.5" },
	De = { class: "flex min-w-0 items-center gap-2" },
	Ye = { class: "truncate text-p-base text-ink-gray-8" },
	Ie = { class: "nums shrink-0 text-base text-ink-gray-5" },
	ze = { class: "flex items-center justify-between gap-3" },
	Te = { key: 0, class: "nums text-p-base text-ink-gray-7" },
	Je = { class: "ml-auto flex gap-2" },
	I = 5,
	z = 10,
	Ze = {
		__name: "RequestDialog",
		props: {
			open: Boolean,
			type: { type: String, required: !0 },
			request: { type: Object, default: null },
			currency: { type: String, default: null },
		},
		emits: ["update:open", "saved"],
		setup(a, { emit: o }) {
			const n = a,
				w = o,
				m = B(null),
				i = he({}),
				y = B([]),
				V = B([]),
				g = B([]),
				C = B(null),
				O = B(!1),
				E = _(() => {
					var e;
					return !!((e = n.request) != null && e.name);
				}),
				L = _({ get: () => n.open, set: (e) => w("update:open", e) }),
				te = _(() => {
					var t;
					const e = ((t = m.value) == null ? void 0 : t.label) || "Request";
					return E.value ? `Edit ${e}` : `New ${e}`;
				}),
				j = _(() => {
					var e;
					return (((e = m.value) == null ? void 0 : e.fields) || []).filter(
						(t) => t.type !== "table",
					);
				}),
				f = _(() => {
					var e;
					return (((e = m.value) == null ? void 0 : e.fields) || []).find(
						(t) => t.type === "table",
					);
				}),
				D = _(() => V.value.filter((e) => !g.value.includes(e.name))),
				T = _(() => {
					const e = f.value;
					if (!e) return null;
					const t = e.fields.find((l) => l.type === "number");
					return t
						? (i[e.fieldname] || []).reduce(
								(l, s) => l + (Number(s[t.fieldname]) || 0),
								0,
						  )
						: null;
				});
			function J() {
				return Object.fromEntries(
					f.value.fields.map((e) => [e.fieldname, e.type === "checkbox" ? !1 : ""]),
				);
			}
			function le() {
				i[f.value.fieldname].push(J());
			}
			function ae() {
				var t, l;
				const e = ((t = n.request) == null ? void 0 : t.values) || {};
				for (const s of Object.keys(i)) delete i[s];
				for (const s of j.value) {
					const d = e[s.fieldname];
					i[s.fieldname] = s.type === "checkbox" ? !!d : d != null ? d : "";
				}
				if (f.value) {
					const s = e[f.value.fieldname];
					i[f.value.fieldname] =
						s != null && s.length
							? s.map((d) =>
									Object.fromEntries(
										f.value.fields.map((x) => {
											var X;
											return [
												x.fieldname,
												(X = d[x.fieldname]) != null ? X : "",
											];
										}),
									),
							  )
							: [J()];
				}
				(V.value = ((l = n.request) == null ? void 0 : l.attachments) || []),
					(y.value = []),
					(g.value = []);
			}
			ye(
				() => [n.open, n.type],
				(t) =>
					Y(this, [t], function* ([e]) {
						e && ((m.value = yield Ve.fetch({ request_type: n.type })), ae());
					}),
				{ immediate: !0 },
			);
			function se(e) {
				return e >= 1024 * 1024
					? `${(e / (1024 * 1024)).toFixed(1)} MB`
					: `${Math.max(1, Math.round(e / 1024))} KB`;
			}
			function ne(e) {
				for (const t of e.target.files) {
					if (D.value.length + y.value.length >= I) {
						U("Too many files", `You can attach at most ${I} files.`);
						break;
					}
					if (t.size > z * 1024 * 1024) {
						U("File too large", `${t.name} is over ${z} MB.`);
						continue;
					}
					y.value.push(t);
				}
				e.target.value = "";
			}
			function oe(e) {
				return new Promise((t, l) => {
					const s = new FileReader();
					(s.onload = () => t(String(s.result).split(",")[1])),
						(s.onerror = () => l(new Error(`Could not read ${e.name}`))),
						s.readAsDataURL(e);
				});
			}
			function P() {
				L.value = !1;
			}
			function re() {
				var t;
				for (const l of j.value)
					if (l.required && !String((t = i[l.fieldname]) != null ? t : "").trim())
						return `${l.label} is required`;
				const e = f.value;
				if (e)
					for (const [l, s] of (i[e.fieldname] || []).entries())
						for (const d of e.fields) {
							if (!d.required) continue;
							const x = s[d.fieldname];
							if (
								d.type === "number"
									? !(Number(x) > 0)
									: !String(x != null ? x : "").trim()
							)
								return `${d.label} is required for ${e.row_label.toLowerCase()} ${
									l + 1
								}`;
						}
				return null;
			}
			function ie() {
				return Y(this, null, function* () {
					const e = re();
					if (e) {
						U("Incomplete form", e);
						return;
					}
					O.value = !0;
					try {
						const t = [];
						for (const s of y.value)
							t.push({ filename: s.name, content: yield oe(s) });
						const l = {
							request_type: n.type,
							values: JSON.stringify(i),
							attachments: JSON.stringify(t),
						};
						E.value
							? (yield Se.submit(
									Q(H({}, l), {
										name: n.request.name,
										removed_attachments: JSON.stringify(g.value),
									}),
							  ),
							  Z(`${m.value.label} updated`))
							: (yield Ce.submit(l),
							  Z(`${m.value.label} saved`, "It is now with your approver.")),
							w("saved"),
							P();
					} catch (t) {
						U("Could not save", ke(t, "Try again in a moment."));
					} finally {
						O.value = !1;
					}
				});
			}
			return (e, t) => (
				r(),
				A(
					c(be),
					{
						modelValue: L.value,
						"onUpdate:modelValue": t[1] || (t[1] = (l) => (L.value = l)),
						options: { title: te.value, size: f.value ? "lg" : "md" },
					},
					{
						"body-content": b(() => [
							m.value
								? (r(),
								  u("div", Fe, [
										j.value.length
											? (r(),
											  u("div", Re, [
													(r(!0),
													u(
														S,
														null,
														R(
															j.value,
															(l) => (
																r(),
																u(
																	"div",
																	{
																		key: l.fieldname,
																		class: W(
																			l.full &&
																				"sm:col-span-2",
																		),
																	},
																	[
																		p(
																			ee,
																			{
																				modelValue:
																					i[l.fieldname],
																				"onUpdate:modelValue":
																					(s) =>
																						(i[
																							l.fieldname
																						] = s),
																				field: l,
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
										f.value
											? (r(),
											  u(
													S,
													{ key: 1 },
													[
														(r(!0),
														u(
															S,
															null,
															R(
																i[f.value.fieldname],
																(l, s) => (
																	r(),
																	u(
																		"div",
																		{
																			key: s,
																			class: "flex flex-col gap-3 rounded-lg border border-outline-gray-2 p-3",
																		},
																		[
																			v("div", Me, [
																				v(
																					"span",
																					Ne,
																					h(
																						f.value
																							.row_label,
																					) +
																						" " +
																						h(s + 1),
																					1,
																				),
																				i[
																					f.value
																						.fieldname
																				].length > 1
																					? (r(),
																					  A(
																							c(q),
																							{
																								key: 0,
																								variant:
																									"ghost",
																								"aria-label": `Remove ${f.value.row_label.toLowerCase()}`,
																								onClick:
																									(
																										d,
																									) =>
																										i[
																											f
																												.value
																												.fieldname
																										].splice(
																											s,
																											1,
																										),
																							},
																							{
																								icon: b(
																									() => [
																										p(
																											c(
																												$,
																											),
																											{
																												name: "trash-2",
																												class: "h-3.5 w-3.5",
																											},
																										),
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
																			v("div", je, [
																				(r(!0),
																				u(
																					S,
																					null,
																					R(
																						f.value
																							.fields,
																						(d) => (
																							r(),
																							u(
																								"div",
																								{
																									key: d.fieldname,
																									class: W(
																										d.full &&
																											"sm:col-span-3",
																									),
																								},
																								[
																									p(
																										ee,
																										{
																											modelValue:
																												l[
																													d
																														.fieldname
																												],
																											"onUpdate:modelValue":
																												(
																													x,
																												) =>
																													(l[
																														d.fieldname
																													] =
																														x),
																											field: d,
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
														p(
															c(q),
															{
																variant: "subtle",
																class: "self-start",
																onClick: le,
															},
															{
																prefix: b(() => [
																	p(c($), {
																		name: "plus",
																		class: "h-3.5 w-3.5",
																	}),
																]),
																default: b(() => [
																	F(
																		" Add Another " +
																			h(f.value.row_label),
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
											  u("div", Ue, [
													t[4] ||
														(t[4] = v(
															"span",
															{
																class: "text-base font-medium text-ink-gray-5",
															},
															"Attachments",
															-1,
														)),
													D.value.length
														? (r(),
														  u("ul", Ae, [
																(r(!0),
																u(
																	S,
																	null,
																	R(
																		D.value,
																		(l) => (
																			r(),
																			u(
																				"li",
																				{
																					key: l.name,
																					class: "flex items-center justify-between gap-2 rounded border border-outline-gray-2 px-2 py-1.5",
																				},
																				[
																					v(
																						"a",
																						{
																							href: l.file_url,
																							target: "_blank",
																							rel: "noopener",
																							class: "flex min-w-0 items-center gap-2 text-p-base text-ink-gray-8 hover:underline",
																						},
																						[
																							p(
																								c(
																									$,
																								),
																								{
																									name: "paperclip",
																									class: "h-3.5 w-3.5 shrink-0 text-ink-gray-4",
																								},
																							),
																							v(
																								"span",
																								Ee,
																								h(
																									l.file_name,
																								),
																								1,
																							),
																						],
																						8,
																						Oe,
																					),
																					p(
																						c(q),
																						{
																							class: "shrink-0",
																							variant:
																								"ghost",
																							"aria-label":
																								"Remove attachment",
																							onClick:
																								(
																									s,
																								) =>
																									g.value.push(
																										l.name,
																									),
																						},
																						{
																							icon: b(
																								() => [
																									p(
																										c(
																											$,
																										),
																										{
																											name: "x",
																											class: "h-3.5 w-3.5",
																										},
																									),
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
													y.value.length
														? (r(),
														  u("ul", Le, [
																(r(!0),
																u(
																	S,
																	null,
																	R(
																		y.value,
																		(l, s) => (
																			r(),
																			u(
																				"li",
																				{
																					key:
																						l.name + s,
																					class: "flex items-center justify-between gap-2 rounded border border-outline-gray-2 px-2 py-1.5",
																				},
																				[
																					v("div", De, [
																						p(c($), {
																							name: "paperclip",
																							class: "h-3.5 w-3.5 shrink-0 text-ink-gray-4",
																						}),
																						v(
																							"span",
																							Ye,
																							h(
																								l.name,
																							),
																							1,
																						),
																						v(
																							"span",
																							Ie,
																							h(
																								se(
																									l.size,
																								),
																							),
																							1,
																						),
																					]),
																					p(
																						c(q),
																						{
																							class: "shrink-0",
																							variant:
																								"ghost",
																							"aria-label":
																								"Remove attachment",
																							onClick:
																								(
																									d,
																								) =>
																									y.value.splice(
																										s,
																										1,
																									),
																						},
																						{
																							icon: b(
																								() => [
																									p(
																										c(
																											$,
																										),
																										{
																											name: "x",
																											class: "h-3.5 w-3.5",
																										},
																									),
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
													p(
														c(q),
														{
															variant: "subtle",
															class: "self-start",
															onClick:
																t[0] ||
																(t[0] = (l) => C.value.click()),
														},
														{
															prefix: b(() => [
																p(c($), {
																	name: "paperclip",
																	class: "h-3.5 w-3.5",
																}),
															]),
															default: b(() => [
																t[3] ||
																	(t[3] = F(
																		" Attach Files ",
																		-1,
																	)),
															]),
															_: 1,
														},
													),
													v(
														"input",
														{
															ref_key: "fileInput",
															ref: C,
															type: "file",
															multiple: "",
															class: "hidden",
															accept: "image/png,image/jpeg,image/gif,.pdf,.doc,.docx,.xls,.xlsx,.txt,.csv",
															onChange: ne,
														},
														null,
														544,
													),
													v(
														"p",
														{ class: "text-base text-ink-gray-5" },
														" Up to " +
															h(I) +
															" files, " +
															h(z) +
															" MB each. ",
													),
											  ]))
											: k("", !0),
										t[5] ||
											(t[5] = v(
												"p",
												{ class: "text-base text-ink-gray-5" },
												" Saved as a draft. Your approver reviews and submits it. ",
												-1,
											)),
								  ]))
								: (r(),
								  u("div", Be, [
										p(c(ge), { class: "h-4 w-4" }),
										t[2] || (t[2] = F(" Loading ", -1)),
								  ])),
						]),
						actions: b(() => [
							v("div", ze, [
								T.value !== null
									? (r(),
									  u(
											"span",
											Te,
											" Total " +
												h(c(xe)(T.value, { currency: a.currency })),
											1,
									  ))
									: k("", !0),
								v("div", Je, [
									p(
										c(q),
										{ variant: "subtle", onClick: P },
										{
											default: b(() => [
												...(t[6] || (t[6] = [F("Cancel", -1)])),
											]),
											_: 1,
										},
									),
									p(
										c(q),
										{
											variant: "solid",
											loading: O.value,
											disabled: !m.value,
											onClick: ie,
										},
										{
											default: b(() => [
												F(h(E.value ? "Save Changes" : "Save"), 1),
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
					["modelValue", "options"],
				)
			);
		},
	};
export { Ze as _, He as a, Ve as b, Qe as d, We as r };
