var B = (N, b, f) =>
	new Promise((h, v) => {
		var l = (n) => {
				try {
					k(f.next(n));
				} catch (x) {
					v(x);
				}
			},
			_ = (n) => {
				try {
					k(f.throw(n));
				} catch (x) {
					v(x);
				}
			},
			k = (n) => (n.done ? h(n.value) : Promise.resolve(n.value).then(l, _));
		k((f = f.apply(N, b)).next());
	});
import {
	L as G,
	v as H,
	o as s,
	d as u,
	w as r,
	h as d,
	f as o,
	g as y,
	I as z,
	k as D,
	z as m,
	e as c,
	F as w,
	i as S,
	R as J,
	t as R,
	u as O,
	a as p,
	S as P,
	B as A,
	b as Q,
} from "./frappe-ui-rHlwnvVy.js";
import { a as W, _ as g, b as X } from "./SectionCard-0tgyDAFI.js";
import { _ as Z } from "./DashGrid-Cmnm2mAO.js";
import { _ as ee } from "./DataTable-BY05XQx8.js";
import { _ as te } from "./StatTiles-DcUJsMoQ.js";
import { _ as ae } from "./StatusBadge-ZWn2FvVw.js";
import { _ as T } from "./FieldRow-C13lI4HG.js";
import { _ as le } from "./EmptyState-0_BFjfJU.js";
import { _ as se, a as q, b as re, d as ne } from "./RequestDialog-CkjqgI3z.js";
import { d as $, a as F } from "./index-6wvshjQq.js";
import { a as ue, e as ie, n as oe } from "./toast-BxUFHbEO.js";
import "./RequestField-DnRQOkWG.js";
import "./DateField-c9rL8vfk.js";
const de = { class: "flex flex-col" },
	me = { key: 0 },
	ce = ["href"],
	pe = { class: "truncate" },
	fe = { class: "nums shrink-0 text-base text-ink-gray-5" },
	ve = { key: 1, class: "px-3.5 pb-3.5" },
	_e = { class: "flex flex-col" },
	ye = { key: 0, class: "text-base text-ink-gray-5" },
	be = { class: "flex flex-col" },
	Ne = {
		__name: "Request",
		setup(N) {
			const b = O(),
				f = Q(),
				h = A(!1),
				v = A(null),
				l = p(() => q.data),
				_ = p(() => {
					var e;
					return (((e = v.value) == null ? void 0 : e.fields) || []).find(
						(t) => t.type === "table",
					);
				}),
				k = p(() => {
					var e;
					return (((e = v.value) == null ? void 0 : e.fields) || []).filter(
						(t) => t.type !== "table",
					);
				}),
				n = p(() => {
					var e, t;
					return _.value
						? (t = (e = l.value) == null ? void 0 : e.values) == null
							? void 0
							: t[_.value.fieldname]
						: null;
				}),
				x = p(() => {
					var e;
					return ((e = _.value) == null ? void 0 : e.label) || "Items";
				}),
				L = p(() => {
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
				I = p(() => {
					if (!l.value) return [];
					const e = l.value.summary
						.slice(0, 3)
						.map((t) => ({ label: t.label, value: M(t) }));
					return (
						e.push({
							label: "Status",
							value: l.value.display_status,
							hint: l.value.editable ? "with your approver" : "",
						}),
						e.slice(0, 4)
					);
				});
			function M(e) {
				var t, a;
				return e.kind === "money"
					? F(e.value, {
							currency: e.currency || ((t = l.value) == null ? void 0 : t.currency),
					  })
					: e.kind === "date"
					  ? $(e.value)
					  : (a = e.value) != null
					    ? a
					    : "—";
			}
			function Y(e, t) {
				var i;
				const a = t[e.key];
				return a == null || a === ""
					? "—"
					: e.fieldType === "date"
					  ? $(a)
					  : e.fieldType === "number"
					    ? F(a, { currency: (i = l.value) == null ? void 0 : i.currency })
					    : a;
			}
			function j(e) {
				var a, i, E;
				const t =
					(i = (a = l.value) == null ? void 0 : a.values) == null
						? void 0
						: i[e.fieldname];
				return e.type === "checkbox"
					? t
						? "Yes"
						: "No"
					: e.type === "date"
					  ? t
							? $(t)
							: ""
					  : e.type === "number"
					    ? F(t, { currency: (E = l.value) == null ? void 0 : E.currency })
					    : t;
			}
			function K(e) {
				return e
					? e >= 1024 * 1024
						? `${(e / (1024 * 1024)).toFixed(1)} MB`
						: `${Math.max(1, Math.round(e / 1024))} KB`
					: "—";
			}
			function C() {
				return B(this, null, function* () {
					const { type: e, name: t } = b.params;
					q.fetch({ request_type: e, name: t }),
						(v.value = yield re.fetch({ request_type: e }));
				});
			}
			function U() {
				const { label: e, name: t, type: a, list_route: i } = l.value;
				P.confirm({
					title: `Delete this ${e.toLowerCase()}?`,
					message: `${t} will be removed. This cannot be undone.`,
					theme: "red",
					confirmLabel: "Delete",
					onConfirm() {
						return B(this, null, function* () {
							try {
								yield ne.submit({ request_type: a, name: t });
							} catch (V) {
								throw (ue("Could not delete", ie(V, "Try again in a moment.")), V);
							}
							oe(`${e} deleted`), f.push(i);
						});
					},
				});
			}
			return (
				G(C),
				H(() => [b.params.type, b.params.name], C),
				(e, t) => (
					s(),
					u(
						X,
						{ loading: y(q).loading && !y(q).data },
						{
							default: r(() => [
								l.value
									? (s(),
									  d(
											w,
											{ key: 0 },
											[
												o(
													W,
													{
														subtitle: `${
															l.value.editable
																? "Raised"
																: "Submitted"
														} ${y($)(l.value.posting_date)}`,
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
																		y(z),
																		{
																			key: 0,
																			variant: "ghost",
																			theme: "red",
																			onClick: U,
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
																: m("", !0),
															l.value.editable
																? (s(),
																  u(
																		y(z),
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
																: m("", !0),
														]),
														_: 1,
													},
													8,
													["subtitle", "crumbs"],
												),
												o(te, { tiles: I.value }, null, 8, ["tiles"]),
												o(Z, null, {
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
																			o(
																				ee,
																				{
																					columns:
																						L.value,
																					rows: n.value,
																					"id-key":
																						"idx",
																				},
																				J({ _: 2 }, [
																					S(
																						L.value,
																						(a) => ({
																							name: `cell-${a.key}`,
																							fn: r(
																								({
																									row: i,
																								}) => [
																									D(
																										R(
																											Y(
																												a,
																												i,
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
																			c("dl", de, [
																				(s(!0),
																				d(
																					w,
																					null,
																					S(
																						k.value,
																						(a) => (
																							s(),
																							u(
																								T,
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
																				  d("ul", me, [
																						(s(!0),
																						d(
																							w,
																							null,
																							S(
																								l
																									.value
																									.attachments,
																								(
																									a,
																								) => (
																									s(),
																									d(
																										"li",
																										{
																											key: a.name,
																											class: "flex items-center justify-between gap-3 border-b border-outline-gray-1 px-3.5 py-2.5 last:border-0",
																										},
																										[
																											c(
																												"a",
																												{
																													href: a.file_url,
																													target: "_blank",
																													rel: "noopener",
																													class: "flex min-w-0 items-center gap-2 text-p-base text-ink-gray-8 hover:underline",
																												},
																												[
																													t[4] ||
																														(t[4] =
																															c(
																																"span",
																																{
																																	class: "h-3.5 w-3.5 shrink-0 text-ink-gray-4 lucide-paperclip",
																																	"aria-hidden":
																																		"true",
																																},
																																null,
																																-1,
																															)),
																													c(
																														"span",
																														pe,
																														R(
																															a.file_name,
																														),
																														1,
																													),
																												],
																												8,
																												ce,
																											),
																											c(
																												"span",
																												fe,
																												R(
																													K(
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
																				  d("div", ve, [
																						o(le, {
																							message:
																								"Nothing attached.",
																						}),
																				  ])),
																		]),
																		_: 1,
																	},
															  ))
															: m("", !0),
													]),
													side: r(() => [
														o(
															g,
															{ title: "Status" },
															{
																action: r(() => [
																	o(
																		ae,
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
																	c("dl", _e, [
																		l.value.approver_name
																			? (s(),
																			  u(
																					T,
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
																			: m("", !0),
																		o(
																			T,
																			{
																				label: "Raised on",
																				value: y($)(
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
																		  d(
																				"p",
																				ye,
																				" This is still a draft. Your approver reviews and submits it. ",
																		  ))
																		: m("", !0),
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
																			c("dl", be, [
																				(s(!0),
																				d(
																					w,
																					null,
																					S(
																						l.value
																							.summary,
																						(a) => (
																							s(),
																							u(
																								T,
																								{
																									key: a.label,
																									label: a.label,
																									value: M(
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
															: m("", !0),
													]),
													_: 1,
												}),
												o(
													se,
													{
														open: h.value,
														"onUpdate:open":
															t[1] || (t[1] = (a) => (h.value = a)),
														type: l.value.type,
														request: l.value,
														currency: l.value.currency,
														onSaved: C,
													},
													null,
													8,
													["open", "type", "request", "currency"],
												),
											],
											64,
									  ))
									: m("", !0),
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
export { Ne as default };
