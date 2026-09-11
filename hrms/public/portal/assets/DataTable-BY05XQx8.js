var W = Object.defineProperty;
var I = Object.getOwnPropertySymbols;
var X = Object.prototype.hasOwnProperty,
	Z = Object.prototype.propertyIsEnumerable;
var T = (a, e, t) =>
		e in a
			? W(a, e, { enumerable: !0, configurable: !0, writable: !0, value: t })
			: (a[e] = t),
	B = (a, e) => {
		for (var t in e || (e = {})) X.call(e, t) && T(a, t, e[t]);
		if (I) for (var t of I(e)) Z.call(e, t) && T(a, t, e[t]);
		return a;
	};
import {
	a5 as ee,
	a6 as te,
	a7 as S,
	a8 as E,
	o as f,
	h,
	Y as k,
	a9 as Y,
	aa as R,
	B as N,
	a as g,
	ab as ae,
	d as H,
	g as v,
	s as P,
	w as b,
	f as _,
	T as q,
	ac as Q,
	P as x,
	Q as A,
	z as L,
	ad as le,
	ae as se,
	M as G,
	e as F,
	af as ne,
	ag as re,
	ah as ie,
	ai as V,
	v as oe,
	i as j,
	F as M,
	aj as ue,
	k as z,
	t as D,
} from "./frappe-ui-rHlwnvVy.js";
import { _ as ce } from "./EmptyState-0_BFjfJU.js";
const J = Symbol("frappe-ui:list");
function de(a) {
	te(J, a);
}
function K() {
	return ee(J, null);
}
const ve = ["role"],
	fe = S({
		__name: "List",
		props: R(
			{ columns: {}, divider: {}, selectable: { type: Boolean }, rowHeight: {} },
			{
				selection: { default: () => [] },
				selectionModifiers: {},
				active: {},
				activeModifiers: {},
			},
		),
		emits: ["update:selection", "update:active"],
		setup(a) {
			const e = a,
				t = E(a, "selection"),
				l = E(a, "active"),
				r = ae(),
				d = g(() => {
					var i;
					return (
						"onUpdate:active" in
						((i = r == null ? void 0 : r.vnode.props) != null ? i : {})
					);
				}),
				c = N(!1),
				s = g(() =>
					B(
						B(
							B(
								{},
								e.columns ? { "--list-columns-default": e.columns.join(" ") } : {},
							),
							e.selectable ? { "--list-checkbox-width": "32px" } : {},
						),
						e.rowHeight ? { "--list-row-height": `${e.rowHeight}px` } : {},
					),
				);
			function u(i) {
				return t.value.includes(i);
			}
			function o(i) {
				t.value = u(i) ? t.value.filter((C) => C !== i) : [...t.value, i];
			}
			function p(i) {
				return l.value === i;
			}
			function y(i) {
				l.value = i;
			}
			const n = N([]);
			function w(i) {
				n.value = i;
			}
			const m = g(() => {
				const i = n.value;
				if (!i.length) return "none";
				const C = i.filter((O) => t.value.includes(O)).length;
				return C === 0 ? "none" : C === i.length ? "all" : "some";
			});
			function $() {
				if (m.value === "all") {
					const i = new Set(n.value);
					t.value = t.value.filter((C) => !i.has(C));
				} else t.value = [...new Set([...t.value, ...n.value])];
			}
			return (
				de({
					divider: g(() => {
						var i;
						return (i = e.divider) != null ? i : e.columns ? "full" : "inset";
					}),
					selectable: g(() => !!e.selectable),
					rowHeight: g(() => e.rowHeight),
					hasHeader: c,
					isSelected: u,
					toggleSelection: o,
					activatable: d,
					isActive: p,
					activate: y,
					setAllValues: w,
					selectAllState: m,
					toggleSelectAll: $,
				}),
				(i, C) => (
					f(),
					h(
						"div",
						{
							"data-slot": "list",
							role: c.value ? "table" : "list",
							style: Y(s.value),
						},
						[k(i.$slots, "default")],
						12,
						ve,
					)
				)
			);
		},
	}),
	me = ["aria-checked", "onKeydown"],
	U = S({
		__name: "ListRowBase",
		props: { tag: {}, value: {} },
		setup(a) {
			const e = S({
					props: { tag: { type: String, required: !0 } },
					setup(p, { slots: y }) {
						return () => {
							var n;
							return le(p.tag, null, (n = y.default) == null ? void 0 : n.call(y));
						};
					},
				}),
				t = a,
				l = K(),
				r = g(() => {
					var p;
					return (p = l == null ? void 0 : l.divider.value) != null ? p : "inset";
				}),
				d = g(() => !!(l != null && l.selectable.value) && t.value !== void 0),
				c = g(() => d.value && !!(l != null && l.isSelected(t.value))),
				s = g(
					() =>
						!!(l != null && l.activatable.value) &&
						t.value !== void 0 &&
						!!(l != null && l.isActive(t.value)),
				),
				u = g(() => t.tag !== "div" || d.value || s.value);
			function o() {
				t.value !== void 0 && (l == null || l.toggleSelection(t.value));
			}
			return (p, y) => {
				var n;
				return (
					f(),
					H(
						v(e),
						{
							tag: a.tag,
							"data-slot": "list-row",
							role: (n = v(l)) != null && n.hasHeader.value ? "row" : "listitem",
							"data-interactive": u.value || void 0,
							"data-state": c.value ? "selected" : void 0,
							"data-active": s.value || void 0,
							"aria-current": s.value || void 0,
							type: a.tag === "button" ? "button" : void 0,
							class: P([
								u.value && "cursor-pointer select-none sm:rounded-[10px]",
								s.value
									? "bg-surface-gray-3"
									: u.value &&
									  "active:bg-surface-gray-2 sm:hover:bg-surface-gray-1",
							]),
						},
						{
							default: b(() => [
								k(p.$slots, "default"),
								_(
									q,
									{
										"enter-active-class":
											"transition-transform duration-75 ease-out",
										"leave-active-class":
											"transition-transform duration-75 ease-out",
										"enter-from-class": "scale-0",
										"leave-to-class": "scale-0",
									},
									{
										default: b(() => [
											d.value
												? (f(),
												  h(
														"div",
														{
															key: 0,
															"data-slot": "list-row-checkbox",
															role: "checkbox",
															"aria-checked": c.value,
															tabindex: "0",
															onClick: A(o, ["stop", "prevent"]),
															onKeydown: [
																x(A(o, ["prevent"]), ["enter"]),
																x(A(o, ["prevent"]), ["space"]),
															],
														},
														[
															_(
																Q,
																{
																	modelValue: c.value,
																	tabindex: "-1",
																	"aria-hidden": "true",
																	class: "pointer-events-none",
																},
																null,
																8,
																["modelValue"],
															),
														],
														40,
														me,
												  ))
												: L("", !0),
										]),
										_: 1,
									},
								),
								r.value !== "none"
									? (f(),
									  h(
											"div",
											{
												key: 0,
												"data-slot": "list-divider",
												"aria-hidden": "true",
												class: "border-t border-outline-gray-1 transition-opacity",
												style: Y({
													gridColumn:
														r.value === "inset" ? "2 / -1" : "1 / -1",
												}),
											},
											null,
											4,
									  ))
									: L("", !0),
							]),
							_: 3,
						},
						8,
						[
							"tag",
							"role",
							"data-interactive",
							"data-state",
							"data-active",
							"aria-current",
							"type",
							"class",
						],
					)
				);
			};
		},
	}),
	ge = S({
		__name: "ListRow",
		props: { to: {}, value: {}, onClick: { type: Function } },
		setup(a) {
			const e = a,
				t = K();
			function l() {
				return !!e.onClick || !!(t != null && t.activatable.value);
			}
			function r(d, c) {
				var s;
				if (t != null && t.selectable.value && e.value !== void 0) {
					d.preventDefault(), t.toggleSelection(e.value);
					return;
				}
				t != null && t.activatable.value && e.value !== void 0 && t.activate(e.value),
					(s = e.onClick) == null || s.call(e, d),
					c == null || c(d);
			}
			return (d, c) =>
				a.to
					? (f(),
					  H(
							v(se),
							{ key: 0, to: a.to, custom: "" },
							{
								default: b(({ href: s, navigate: u }) => [
									_(
										U,
										{
											tag: "a",
											href: s,
											value: a.value,
											onClick: (o) => r(o, u),
										},
										{ default: b(() => [k(d.$slots, "default")]), _: 3 },
										8,
										["href", "value", "onClick"],
									),
								]),
								_: 3,
							},
							8,
							["to"],
					  ))
					: (f(),
					  H(
							U,
							{ key: 1, tag: l() ? "button" : "div", value: a.value, onClick: r },
							{ default: b(() => [k(d.$slots, "default")]), _: 3 },
							8,
							["tag", "value"],
					  ));
		},
	}),
	ye = ["role"],
	he = S({
		__name: "ListCell",
		setup(a) {
			const e = K();
			return (t, l) => {
				var r;
				return (
					f(),
					h(
						"div",
						{
							"data-slot": "list-cell",
							role: (r = v(e)) != null && r.hasHeader.value ? "cell" : void 0,
							class: "flex min-w-0 items-center",
						},
						[k(t.$slots, "default")],
						8,
						ye,
					)
				);
			};
		},
	}),
	pe = { "data-slot": "list-header", role: "row", class: "h-8 text-sm text-ink-gray-5" },
	be = ["aria-checked"],
	ke = S({
		__name: "ListHeader",
		setup(a) {
			const e = K(),
				t = g(() => {
					const l = e == null ? void 0 : e.selectAllState.value;
					return l === "all" ? "true" : l === "some" ? "mixed" : "false";
				});
			return (
				e &&
					((e.hasHeader.value = !0),
					G(() => {
						e.hasHeader.value = !1;
					})),
				(l, r) => (
					f(),
					h("div", pe, [
						k(l.$slots, "default"),
						_(
							q,
							{
								"enter-active-class": "transition-transform duration-75 ease-out",
								"leave-active-class": "transition-transform duration-75 ease-out",
								"enter-from-class": "scale-0",
								"leave-to-class": "scale-0",
							},
							{
								default: b(() => {
									var d;
									return [
										(d = v(e)) != null && d.selectable.value
											? (f(),
											  h(
													"div",
													{
														key: 0,
														"data-slot": "list-header-checkbox",
														role: "checkbox",
														"aria-checked": t.value,
														"aria-label": "Select all",
														tabindex: "0",
														onClick:
															r[0] ||
															(r[0] = A(
																(...c) =>
																	v(e).toggleSelectAll &&
																	v(e).toggleSelectAll(...c),
																["stop", "prevent"],
															)),
														onKeydown: [
															r[1] ||
																(r[1] = x(
																	A(
																		(...c) =>
																			v(e).toggleSelectAll &&
																			v(e).toggleSelectAll(
																				...c,
																			),
																		["prevent"],
																	),
																	["enter"],
																)),
															r[2] ||
																(r[2] = x(
																	A(
																		(...c) =>
																			v(e).toggleSelectAll &&
																			v(e).toggleSelectAll(
																				...c,
																			),
																		["prevent"],
																	),
																	["space"],
																)),
														],
													},
													[
														_(
															Q,
															{
																modelValue:
																	v(e).selectAllState.value ===
																	"all",
																indeterminate:
																	v(e).selectAllState.value ===
																	"some",
																tabindex: "-1",
																"aria-hidden": "true",
																class: "pointer-events-none",
															},
															null,
															8,
															["modelValue", "indeterminate"],
														),
													],
													40,
													be,
											  ))
											: L("", !0),
									];
								}),
								_: 1,
							},
						),
						r[3] ||
							(r[3] = F(
								"div",
								{
									"data-slot": "list-header-border",
									"aria-hidden": "true",
									class: "border-b border-outline-gray-1",
								},
								null,
								-1,
							)),
					])
				)
			);
		},
	}),
	we = {
		"data-slot": "list-header-cell",
		role: "columnheader",
		class: "flex min-w-0 items-center gap-1",
	},
	_e = { key: 0, class: "shrink-0" },
	$e = { class: "truncate" },
	Se = { key: 1, class: "shrink-0" },
	Ce = S({
		__name: "ListHeaderCell",
		setup(a) {
			return (e, t) => (
				f(),
				h("div", we, [
					e.$slots.prefix ? (f(), h("span", _e, [k(e.$slots, "prefix")])) : L("", !0),
					F("span", $e, [k(e.$slots, "default")]),
					e.$slots.suffix ? (f(), h("span", Se, [k(e.$slots, "suffix")])) : L("", !0),
				])
			);
		},
	});
function He(a, e) {
	var s;
	const t = g(() => V(a)),
		{
			list: l,
			containerProps: r,
			wrapperProps: d,
		} = ne(t, {
			itemHeight: () => V(e.itemHeight),
			overscan: (s = e.overscan) != null ? s : 6,
		}),
		c = N(null);
	return (
		re(() => {
			var o;
			if (!V((o = e.enabled) != null ? o : !0)) {
				r.ref.value = null;
				return;
			}
			const u = V(e.scrollContainer);
			r.ref.value = u != null ? u : Ae(c.value);
		}),
		ie(
			() => {
				var u;
				return V((u = e.enabled) != null ? u : !0) ? r.ref.value : null;
			},
			"scroll",
			() => r.onScroll(),
		),
		{ rows: l, wrapperProps: d, anchor: c }
	);
}
function Ae(a) {
	var t;
	let e = (t = a == null ? void 0 : a.parentElement) != null ? t : null;
	for (; e; ) {
		const { overflowY: l } = getComputedStyle(e);
		if (l === "auto" || l === "scroll" || l === "overlay") return e;
		e = e.parentElement;
	}
	return null;
}
const Ve = S({
		__name: "ListRows",
		props: {
			items: {},
			rowKey: { type: [String, Function] },
			virtual: { type: [Boolean, Object] },
		},
		setup(a) {
			const e = a,
				t = K(),
				l = g(() => {
					const n = typeof e.virtual == "object" ? e.virtual.itemHeight : void 0;
					return n != null ? n : t == null ? void 0 : t.rowHeight.value;
				}),
				r = g(() =>
					e.virtual
						? l.value
							? !0
							: (console.warn(
									"[frappe-ui] <ListRows virtual> needs a row height — set `rowHeight` on <List> or pass `virtual.itemHeight`.",
							  ),
							  !1)
						: !1,
				),
				{
					rows: d,
					wrapperProps: c,
					anchor: s,
				} = He(() => (r.value ? e.items : []), {
					enabled: () => r.value,
					itemHeight: () => {
						var n;
						return (n = l.value) != null ? n : 0;
					},
					overscan: typeof e.virtual == "object" ? e.virtual.overscan : void 0,
				});
			oe(
				() => e.items,
				(n) => {
					t == null || t.setAllValues(n.map((w, m) => u(w, m)));
				},
				{ immediate: !0 },
			),
				G(() => (t == null ? void 0 : t.setAllValues([])));
			function u(n, w) {
				return String(o(n, w));
			}
			function o(n, w) {
				var $;
				if (e.rowKey !== void 0) {
					const i =
						typeof e.rowKey == "function"
							? e.rowKey(n, w)
							: p(n)
							  ? n[e.rowKey]
							  : void 0;
					return y(i) ? i : w;
				}
				if (!p(n)) return w;
				const m = ($ = n.name) != null ? $ : n.id;
				return y(m) ? m : w;
			}
			function p(n) {
				return n !== null && typeof n == "object";
			}
			function y(n) {
				return typeof n == "string" || typeof n == "number" || typeof n == "symbol";
			}
			return (n, w) =>
				r.value
					? (f(),
					  h(
							"div",
							ue({ key: 1, ref_key: "anchor", ref: s }, v(c), {
								role: "presentation",
							}),
							[
								(f(!0),
								h(
									M,
									null,
									j(v(d), (m) =>
										k(
											n.$slots,
											"default",
											{
												item: m.data,
												index: m.index,
												value: u(m.data, m.index),
											},
											void 0,
											void 0,
											u(m.data, m.index),
										),
									),
									128,
								)),
							],
							16,
					  ))
					: (f(!0),
					  h(
							M,
							{ key: 0 },
							j(a.items, (m, $) =>
								k(
									n.$slots,
									"default",
									{ item: m, index: $, value: u(m, $) },
									void 0,
									void 0,
									u(m, $),
								),
							),
							128,
					  ));
		},
	}),
	Le = { class: "truncate" },
	Ke = { key: 1, class: "px-3.5 pb-3.5" },
	Me = {
		__name: "DataTable",
		props: R(
			{
				columns: { type: Array, default: () => [] },
				rows: { type: Array, default: () => [] },
				emptyMessage: { type: String, default: "Nothing here yet." },
				clickable: Boolean,
				selectable: Boolean,
				idKey: { type: String, default: "name" },
			},
			{ selection: { type: Array, default: () => [] }, selectionModifiers: {} },
		),
		emits: R(["row-click"], ["update:selection"]),
		setup(a) {
			const e = a,
				t = E(a, "selection"),
				l = g(() =>
					e.columns.map((s) =>
						s.track
							? s.track
							: s.primary
							  ? "minmax(6rem,2fr)"
							  : s.align === "right" || s.badge
							    ? "minmax(4rem,1fr)"
							    : "minmax(5rem,1fr)",
					),
				);
			function r(s) {
				return [
					s.align === "right" ? "justify-end" : "justify-start",
					!s.primary && !s.badge && "max-sm:hidden",
				];
			}
			function d(s) {
				return [
					...r(s),
					"text-base",
					s.nums && "nums",
					s.muted ? "text-ink-gray-5" : "text-ink-gray-8",
					s.strong && "font-semibold text-ink-gray-9",
				];
			}
			function c(s, u) {
				const o = s == null ? void 0 : s[u.key];
				return o == null || o === "" ? "—" : o;
			}
			return (s, u) =>
				a.rows.length
					? (f(),
					  H(
							v(fe),
							{
								key: 0,
								selection: t.value,
								"onUpdate:selection": u[0] || (u[0] = (o) => (t.value = o)),
								columns: l.value,
								"row-height": 40,
								selectable: a.selectable,
								class: "list-row-px-3.5 max-sm:[--list-columns:minmax(0,1fr)_auto]",
							},
							{
								default: b(() => [
									_(
										v(ke),
										{ class: "max-sm:!hidden" },
										{
											default: b(() => [
												(f(!0),
												h(
													M,
													null,
													j(
														a.columns,
														(o) => (
															f(),
															H(
																v(Ce),
																{
																	key: o.key,
																	class: P([r(o), "text-base"]),
																},
																{
																	default: b(() => [
																		z(D(o.label), 1),
																	]),
																	_: 2,
																},
																1032,
																["class"],
															)
														),
													),
													128,
												)),
											]),
											_: 1,
										},
									),
									_(
										v(Ve),
										{ items: a.rows, "row-key": a.idKey },
										{
											default: b(({ item: o, value: p }) => [
												_(
													v(ge),
													{
														value: p,
														onClick: (y) =>
															a.clickable && s.$emit("row-click", o),
													},
													{
														default: b(() => [
															(f(!0),
															h(
																M,
																null,
																j(
																	a.columns,
																	(y) => (
																		f(),
																		H(
																			v(he),
																			{
																				key: y.key,
																				class: P(d(y)),
																			},
																			{
																				default: b(() => [
																					F("span", Le, [
																						k(
																							s.$slots,
																							`cell-${y.key}`,
																							{
																								row: o,
																							},
																							() => [
																								z(
																									D(
																										c(
																											o,
																											y,
																										),
																									),
																									1,
																								),
																							],
																						),
																					]),
																				]),
																				_: 2,
																			},
																			1032,
																			["class"],
																		)
																	),
																),
																128,
															)),
														]),
														_: 2,
													},
													1032,
													["value", "onClick"],
												),
											]),
											_: 3,
										},
										8,
										["items", "row-key"],
									),
								]),
								_: 3,
							},
							8,
							["selection", "columns", "selectable"],
					  ))
					: (f(),
					  h("div", Ke, [_(ce, { message: a.emptyMessage }, null, 8, ["message"])]));
		},
	};
export { Me as _ };
