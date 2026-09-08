var B = (N, b, p) =>
	new Promise((h, v) => {
		var l = (n) => {
				try {
					k(p.next(n));
				} catch (x) {
					v(x);
				}
			},
			_ = (n) => {
				try {
					k(p.throw(n));
				} catch (x) {
					v(x);
				}
			},
			k = (n) => (n.done ? h(n.value) : Promise.resolve(n.value).then(l, _));
		k((p = p.apply(N, b)).next());
	});
import {
	u as W,
	b as G,
	P as H,
	w as J,
	o as s,
	f as u,
	g as r,
	s as c,
	F as w,
	h as i,
	i as m,
	M as L,
	B as D,
	C as d,
	k as y,
	t as T,
	V as O,
	x as F,
	p as Q,
	a as f,
	W as X,
	e as z,
} from "./frappe-ui-BQ9PgXrr.js";
import { _ as g, a as Z } from "./SectionCard-u_7VCKnT.js";
import { _ as ee } from "./PageHead-3jtDpZ9g.js";
import { _ as te } from "./DashGrid-Bd23iLvt.js";
import { _ as ae } from "./DataTable-vZ6Z-J3d.js";
import { _ as le } from "./StatTiles-YoNxs_Qn.js";
import { _ as se } from "./StatusBadge-Bqz4zlkD.js";
import { _ as q } from "./FieldRow-DbBPtAxY.js";
import { _ as re } from "./EmptyState-DNwecFw5.js";
import { _ as ne, a as C, b as ue, d as ie } from "./RequestDialog-TPB8mqrQ.js";
import { d as $, b as M } from "./index-DKSqIuAQ.js";
import { n as oe, a as ce, e as me } from "./toast-9qekBDJT.js";
const de = { class: "flex flex-col" },
	fe = { key: 0 },
	pe = ["href"],
	ve = { class: "truncate" },
	_e = { class: "nums shrink-0 text-base text-ink-gray-5" },
	ye = { key: 1, class: "px-3.5 pb-3.5" },
	be = { class: "flex flex-col" },
	he = { key: 0, class: "text-base text-ink-gray-5" },
	ke = { class: "flex flex-col" },
	Re = {
		__name: "Request",
		setup(N) {
			const b = W(),
				p = G(),
				h = z(!1),
				v = z(null),
				l = f(() => C.data),
				_ = f(() => {
					var e;
					return (((e = v.value) == null ? void 0 : e.fields) || []).find(
						(t) => t.type === "table",
					);
				}),
				k = f(() => {
					var e;
					return (((e = v.value) == null ? void 0 : e.fields) || []).filter(
						(t) => t.type !== "table",
					);
				}),
				n = f(() => {
					var e, t;
					return _.value
						? (t = (e = l.value) == null ? void 0 : e.values) == null
							? void 0
							: t[_.value.fieldname]
						: null;
				}),
				x = f(() => {
					var e;
					return ((e = _.value) == null ? void 0 : e.label) || "Items";
				}),
				R = f(() => {
					var e;
					return (((e = _.value) == null ? void 0 : e.fields) || []).map((t, a) => ({
						key: t.fieldname,
						label: t.label,
						primary: a === 0,
						nums: t.type === "number" || t.type === "date",
						align: t.type === "number" ? "right" : "left",
						fieldType: t.type,
					}));
				}),
				A = f(() => {
					if (!l.value) return [];
					const e = l.value.summary
						.slice(0, 3)
						.map((t) => ({ label: t.label, value: V(t) }));
					return (
						e.push({
							label: "Status",
							value: l.value.display_status,
							hint: l.value.editable ? "with your approver" : "",
						}),
						e.slice(0, 4)
					);
				});
			function V(e) {
				var t, a;
				return e.kind === "money"
					? M(e.value, {
							currency: e.currency || ((t = l.value) == null ? void 0 : t.currency),
					  })
					: e.kind === "date"
					  ? $(e.value)
					  : (a = e.value) != null
					    ? a
					    : "—";
			}
			function Y(e, t) {
				var o;
				const a = t[e.key];
				return a == null || a === ""
					? "—"
					: e.fieldType === "date"
					  ? $(a)
					  : e.fieldType === "number"
					    ? M(a, { currency: (o = l.value) == null ? void 0 : o.currency })
					    : a;
			}
			function j(e) {
				var a, o, E;
				const t =
					(o = (a = l.value) == null ? void 0 : a.values) == null
						? void 0
						: o[e.fieldname];
				return e.type === "checkbox"
					? t
						? "Yes"
						: "No"
					: e.type === "date"
					  ? t
							? $(t)
							: ""
					  : e.type === "number"
					    ? M(t, { currency: (E = l.value) == null ? void 0 : E.currency })
					    : t;
			}
			function I(e) {
				return e
					? e >= 1024 * 1024
						? `${(e / (1024 * 1024)).toFixed(1)} MB`
						: `${Math.max(1, Math.round(e / 1024))} KB`
					: "—";
			}
			function S() {
				return B(this, null, function* () {
					const { type: e, name: t } = b.params;
					C.fetch({ request_type: e, name: t }),
						(v.value = yield ue.fetch({ request_type: e }));
				});
			}
			function K() {
				const { label: e, name: t, type: a, list_route: o } = l.value;
				X({
					title: `Delete this ${e.toLowerCase()}?`,
					message: `${t} will be removed. This cannot be undone.`,
					onConfirm(Le) {
						return B(this, arguments, function* ({ hideDialog: P }) {
							try {
								yield ie.submit({ request_type: a, name: t }),
									oe(`${e} deleted`),
									P(),
									p.push(o);
							} catch (U) {
								ce("Could not delete", me(U, "Try again in a moment."));
							}
						});
					},
				});
			}
			return (
				H(S),
				J(() => [b.params.type, b.params.name], S),
				(e, t) => (
					s(),
					u(
						Z,
						{ loading: m(C).loading && !m(C).data },
						{
							default: r(() => [
								l.value
									? (s(),
									  c(
											w,
											{ key: 0 },
											[
												i(
													ee,
													{
														subtitle: `${
															l.value.editable
																? "Raised"
																: "Submitted"
														} ${m($)(l.value.posting_date)}`,
														crumbs: [
															{
																label: l.value.label,
																to: l.value.list_route,
															},
															{ label: l.value.name },
														],
													},
													{
														actions: r(() => [
															l.value.editable
																? (s(),
																  u(
																		m(L),
																		{
																			key: 0,
																			variant: "ghost",
																			theme: "red",
																			onClick: K,
																		},
																		{
																			default: r(() => [
																				...(t[2] ||
																					(t[2] = [
																						D(
																							"Delete",
																							-1,
																						),
																					])),
																			]),
																			_: 1,
																		},
																  ))
																: d("", !0),
															l.value.editable
																? (s(),
																  u(
																		m(L),
																		{
																			key: 1,
																			variant: "solid",
																			onClick:
																				t[0] ||
																				(t[0] = (a) =>
																					(h.value =
																						!0)),
																		},
																		{
																			default: r(() => [
																				...(t[3] ||
																					(t[3] = [
																						D(
																							"Edit",
																							-1,
																						),
																					])),
																			]),
																			_: 1,
																		},
																  ))
																: d("", !0),
														]),
														_: 1,
													},
													8,
													["subtitle", "crumbs"],
												),
												i(le, { tiles: A.value }, null, 8, ["tiles"]),
												i(te, null, {
													main: r(() => [
														n.value
															? (s(),
															  u(
																	g,
																	{
																		key: 0,
																		title: x.value,
																		padded: !1,
																	},
																	{
																		default: r(() => [
																			i(
																				ae,
																				{
																					columns:
																						R.value,
																					rows: n.value,
																					"id-key":
																						"idx",
																				},
																				O({ _: 2 }, [
																					T(
																						R.value,
																						(a) => ({
																							name: `cell-${a.key}`,
																							fn: r(
																								({
																									row: o,
																								}) => [
																									D(
																										F(
																											Y(
																												a,
																												o,
																											),
																										),
																										1,
																									),
																								],
																							),
																						}),
																					),
																				]),
																				1032,
																				[
																					"columns",
																					"rows",
																				],
																			),
																		]),
																		_: 1,
																	},
																	8,
																	["title"],
															  ))
															: (s(),
															  u(
																	g,
																	{ key: 1, title: "Details" },
																	{
																		default: r(() => [
																			y("dl", de, [
																				(s(!0),
																				c(
																					w,
																					null,
																					T(
																						k.value,
																						(a) => (
																							s(),
																							u(
																								q,
																								{
																									key: a.fieldname,
																									label: a.label,
																									value: j(
																										a,
																									),
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
															  )),
														l.value.supports_attachments
															? (s(),
															  u(
																	g,
																	{
																		key: 2,
																		title: "Attachments",
																		padded: !1,
																	},
																	{
																		default: r(() => [
																			l.value.attachments
																				.length
																				? (s(),
																				  c("ul", fe, [
																						(s(!0),
																						c(
																							w,
																							null,
																							T(
																								l
																									.value
																									.attachments,
																								(
																									a,
																								) => (
																									s(),
																									c(
																										"li",
																										{
																											key: a.name,
																											class: "flex items-center justify-between gap-3 border-b border-outline-gray-1 px-3.5 py-2.5 last:border-0",
																										},
																										[
																											y(
																												"a",
																												{
																													href: a.file_url,
																													target: "_blank",
																													rel: "noopener",
																													class: "flex min-w-0 items-center gap-2 text-p-base text-ink-gray-8 hover:underline",
																												},
																												[
																													i(
																														m(
																															Q,
																														),
																														{
																															name: "paperclip",
																															class: "h-3.5 w-3.5 shrink-0 text-ink-gray-4",
																														},
																													),
																													y(
																														"span",
																														ve,
																														F(
																															a.file_name,
																														),
																														1,
																													),
																												],
																												8,
																												pe,
																											),
																											y(
																												"span",
																												_e,
																												F(
																													I(
																														a.file_size,
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
																				  ]))
																				: (s(),
																				  c("div", ye, [
																						i(re, {
																							message:
																								"Nothing attached.",
																						}),
																				  ])),
																		]),
																		_: 1,
																	},
															  ))
															: d("", !0),
													]),
													side: r(() => [
														i(
															g,
															{ title: "Status" },
															{
																action: r(() => [
																	i(
																		se,
																		{
																			status: l.value
																				.display_status,
																		},
																		null,
																		8,
																		["status"],
																	),
																]),
																default: r(() => [
																	y("dl", be, [
																		l.value.approver_name
																			? (s(),
																			  u(
																					q,
																					{
																						key: 0,
																						label: "Approver",
																						value: l
																							.value
																							.approver_name,
																					},
																					null,
																					8,
																					["value"],
																			  ))
																			: d("", !0),
																		i(
																			q,
																			{
																				label: "Raised on",
																				value: m($)(
																					l.value
																						.posting_date,
																				),
																				nums: "",
																			},
																			null,
																			8,
																			["value"],
																		),
																	]),
																	l.value.editable
																		? (s(),
																		  c(
																				"p",
																				he,
																				" This is still a draft. Your approver reviews and submits it. ",
																		  ))
																		: d("", !0),
																]),
																_: 1,
															},
														),
														n.value
															? (s(),
															  u(
																	g,
																	{ key: 0, title: "Summary" },
																	{
																		default: r(() => [
																			y("dl", ke, [
																				(s(!0),
																				c(
																					w,
																					null,
																					T(
																						l.value
																							.summary,
																						(a) => (
																							s(),
																							u(
																								q,
																								{
																									key: a.label,
																									label: a.label,
																									value: V(
																										a,
																									),
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
															  ))
															: d("", !0),
													]),
													_: 1,
												}),
												i(
													ne,
													{
														open: h.value,
														"onUpdate:open":
															t[1] || (t[1] = (a) => (h.value = a)),
														type: l.value.type,
														request: l.value,
														currency: l.value.currency,
														onSaved: S,
													},
													null,
													8,
													["open", "type", "request", "currency"],
												),
											],
											64,
									  ))
									: d("", !0),
							]),
							_: 1,
						},
						8,
						["loading"],
					)
				)
			);
		},
	};
export { Re as default };
