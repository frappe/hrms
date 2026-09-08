const __vite__mapDeps = (
	i,
	m = __vite__mapDeps,
	d = m.f ||
		(m.f = [
			"assets/Home-DBGqMnyY.js",
			"assets/SectionCard-u_7VCKnT.js",
			"assets/frappe-ui-BQ9PgXrr.js",
			"assets/frappe-ui-Bp8pEQrW.css",
			"assets/PageHead-3jtDpZ9g.js",
			"assets/DashGrid-Bd23iLvt.js",
			"assets/DataTable-vZ6Z-J3d.js",
			"assets/EmptyState-DNwecFw5.js",
			"assets/StatusBadge-Bqz4zlkD.js",
			"assets/PersonRow-DZ4YBxpS.js",
			"assets/BalanceBars-CBgUe-mJ.js",
			"assets/FieldRow-DbBPtAxY.js",
			"assets/toast-9qekBDJT.js",
			"assets/Attendance-CLV1kRNW.js",
			"assets/StatTiles-YoNxs_Qn.js",
			"assets/RequestDialog-TPB8mqrQ.js",
			"assets/Leave-59X_GT51.js",
			"assets/Expenses-C-UGZDUr.js",
			"assets/Request-B1_U03dg.js",
			"assets/Payslips-BPdeU3Bp.js",
			"assets/Payslip-CFlv2Jvw.js",
			"assets/Advances-D4z4VXmc.js",
			"assets/Directory-CbMhGYpC.js",
			"assets/Colleague-CM8SqR9s.js",
			"assets/IdentityBand-BGB1Buc7.js",
			"assets/OrgChart-B5HV4bG-.js",
			"assets/OrgChart-CRKf-07x.css",
			"assets/Holidays-Bk9m_VhS.js",
			"assets/Documents-B4XK28MO.js",
			"assets/Profile-5WmgxzRt.js",
		]),
) => i.map((i) => d[i]);
var Ce = Object.defineProperty;
var ve = Object.getOwnPropertySymbols;
var Ie = Object.prototype.hasOwnProperty,
	Ye = Object.prototype.propertyIsEnumerable;
var ge = (r, a, i) =>
		a in r
			? Ce(r, a, { enumerable: !0, configurable: !0, writable: !0, value: i })
			: (r[a] = i),
	$e = (r, a) => {
		for (var i in a || (a = {})) Ie.call(a, i) && ge(r, i, a[i]);
		if (ve) for (var i of ve(a)) Ye.call(a, i) && ge(r, i, a[i]);
		return r;
	};
var le = (r, a, i) =>
	new Promise((d, s) => {
		var m = (b) => {
				try {
					_(i.next(b));
				} catch (p) {
					s(p);
				}
			},
			y = (b) => {
				try {
					_(i.throw(b));
				} catch (p) {
					s(p);
				}
			},
			_ = (b) => (b.done ? d(b.value) : Promise.resolve(b.value).then(m, y));
		_((i = i.apply(r, a)).next());
	});
import {
	c as O,
	r as Pe,
	a as te,
	u as he,
	b as Ne,
	d as He,
	e as Oe,
	w as fe,
	o as P,
	f as ce,
	g as Q,
	h as N,
	i as R,
	_ as Ve,
	j as Be,
	k as V,
	l as je,
	m as Fe,
	n as We,
	p as me,
	q as Se,
	s as q,
	F as xe,
	t as Ue,
	v as de,
	x as pe,
	y as Ee,
	z as Te,
	A as qe,
	B as be,
	C as De,
	T as Me,
	D as ze,
	E as Je,
	G as Ke,
	H as Ze,
	I as A,
	J as Ge,
	K as Qe,
	L as Xe,
	M as et,
	N as tt,
	O as nt,
} from "./frappe-ui-BQ9PgXrr.js";
(function () {
	const a = document.createElement("link").relList;
	if (a && a.supports && a.supports("modulepreload")) return;
	for (const s of document.querySelectorAll('link[rel="modulepreload"]')) d(s);
	new MutationObserver((s) => {
		for (const m of s)
			if (m.type === "childList")
				for (const y of m.addedNodes)
					y.tagName === "LINK" && y.rel === "modulepreload" && d(y);
	}).observe(document, { childList: !0, subtree: !0 });
	function i(s) {
		const m = {};
		return (
			s.integrity && (m.integrity = s.integrity),
			s.referrerPolicy && (m.referrerPolicy = s.referrerPolicy),
			s.crossOrigin === "use-credentials"
				? (m.credentials = "include")
				: s.crossOrigin === "anonymous"
				  ? (m.credentials = "omit")
				  : (m.credentials = "same-origin"),
			m
		);
	}
	function d(s) {
		if (s.ep) return;
		s.ep = !0;
		const m = i(s);
		fetch(s.href, m);
	}
})();
const rt = [
		{
			group: "My Work",
			items: [
				{ label: "Home", to: "/home", icon: "home" },
				{ label: "Attendance", to: "/attendance", icon: "clock" },
				{ label: "Leave", to: "/leave", icon: "sunrise" },
				{ label: "Expenses", to: "/expenses", icon: "credit-card", countKey: "expenses" },
				{ label: "Payslips", to: "/payslips", icon: "file-text" },
				{ label: "Advances", to: "/advances", icon: "trending-up" },
			],
		},
		{
			group: "Company",
			items: [
				{ label: "Directory", to: "/directory", icon: "users" },
				{ label: "Org chart", to: "/org-chart", icon: "git-merge" },
				{ label: "Holidays", to: "/holidays", icon: "calendar" },
				{ label: "Documents", to: "/documents", icon: "folder" },
			],
		},
	],
	st = [
		{ label: "Home", to: "/home", icon: "home" },
		{ label: "Attendance", to: "/attendance", icon: "clock" },
		{ label: "Leave", to: "/leave", icon: "sunrise" },
		{ label: "Pay", to: "/payslips", icon: "file-text" },
		{ label: "More", action: "more", icon: "menu" },
	];
function ot() {
	return Object.fromEntries(
		document.cookie
			.split("; ")
			.filter(Boolean)
			.map((r) => {
				const a = r.indexOf("=");
				return [r.slice(0, a), decodeURIComponent(r.slice(a + 1))];
			}),
	);
}
function at() {
	const r = ot().user_id;
	return r && r !== "Guest" ? r : null;
}
const it = O({
		url: "logout",
		onSuccess() {
			(ne.user = null), (window.location.href = "/login");
		},
	}),
	ne = Pe({ user: at(), isLoggedIn: te(() => !!ne.user), logout: it }),
	S = (r) => `hrms.api.portal.${r}`,
	B = O({ url: S("get_bootstrap"), cache: "portal:bootstrap" }),
	Tt = O({ url: S("get_home") }),
	Lt = O({ url: S("get_attendance") }),
	At = O({ url: S("get_leave") }),
	Rt = O({ url: S("get_expenses") }),
	Ct = O({ url: S("get_payslips") }),
	It = O({ url: S("get_payslip") }),
	Yt = O({ url: S("get_advances") }),
	Pt = O({ url: S("get_directory") }),
	Nt = O({ url: S("get_colleague") }),
	Ht = O({ url: S("get_org_chart") }),
	Vt = O({ url: S("get_holidays") }),
	Bt = O({ url: S("get_documents") }),
	jt = O({ url: S("get_profile") }),
	Ft = O({ url: S("get_profile_field_options"), cache: "portal:field-options" }),
	Wt = O({ url: S("update_profile") }),
	Ut = O({ url: S("mark_checkin") }),
	we = {
		__name: "AppSidebar",
		props: { expanded: Boolean },
		emits: ["navigate"],
		setup(r, { emit: a }) {
			const i = r,
				d = a,
				s = he(),
				m = Ne(),
				y = te(() => {
					var f;
					return (f = B.data) == null ? void 0 : f.employee;
				}),
				_ = te(() => {
					var f;
					return ((f = y.value) == null ? void 0 : f.company) || "";
				}),
				b = te(() => {
					var f;
					return ((f = y.value) == null ? void 0 : f.designation) || "Employee";
				}),
				p = te(() => {
					var f;
					return ((f = B.data) == null ? void 0 : f.counts) || {};
				}),
				D = He(Fe).greaterOrEqual("lg"),
				H = Oe(i.expanded ? !1 : !D.value);
			fe(D, (f) => {
				i.expanded || (H.value = !f);
			});
			function C(f) {
				return (g, { attrs: $ }) => We(me, $e({ name: f }, $));
			}
			function I(f) {
				m.push(f), d("navigate");
			}
			const j = te(() =>
					rt.map((f) => ({
						label: f.group,
						items: f.items.map((g) => ({
							label: g.label,
							icon: C(g.icon),
							suffix: W(g) ? String(W(g)) : void 0,
							isActive: J(g.to),
							onClick: () => I(g.to),
						})),
					})),
				),
				z = [{ label: "Log Out", onClick: () => ne.logout.submit() }];
			function W(f) {
				return (f.countKey && p.value[f.countKey]) || 0;
			}
			function J(f) {
				return s.path === f || s.path.startsWith(f + "/");
			}
			return (f, g) => (
				P(),
				ce(
					R(je),
					{
						collapsed: H.value,
						"onUpdate:collapsed": g[1] || (g[1] = ($) => (H.value = $)),
						header: { title: "Frappe HR", subtitle: _.value, menuItems: z },
						sections: j.value,
						"disable-collapse": r.expanded,
					},
					{
						"header-logo": Q(() => [
							...(g[2] ||
								(g[2] = [
									V(
										"div",
										{
											class: "flex h-full w-full items-center justify-center bg-surface-gray-7 text-base font-bold text-ink-white",
										},
										" HR ",
										-1,
									),
								])),
						]),
						"footer-items": Q(() => {
							var $;
							return [
								N(
									R(Ve),
									{
										label:
											(($ = y.value) == null ? void 0 : $.employee_name) ||
											"—",
										suffix: b.value,
										onClick: g[0] || (g[0] = (M) => I("/me")),
									},
									{
										icon: Q(() => {
											var M, F;
											return [
												N(
													R(Be),
													{
														label:
															(M = y.value) == null
																? void 0
																: M.employee_name,
														image:
															(F = y.value) == null
																? void 0
																: F.image,
														size: "md",
													},
													null,
													8,
													["label", "image"],
												),
											];
										}),
										_: 1,
									},
									8,
									["label", "suffix"],
								),
							];
						}),
						_: 1,
					},
					8,
					["collapsed", "header", "sections", "disable-collapse"],
				)
			);
		},
	},
	ut = {
		class: "grid shrink-0 grid-cols-5 border-t border-outline-gray-1 bg-surface-white pb-safe-bottom",
		"aria-label": "Sections",
	},
	ct = ["onClick"],
	lt = { class: "text-[10px]" },
	ke = "flex flex-col items-center gap-0.5 py-2 transition-colors",
	dt = {
		__name: "BottomTabs",
		emits: ["more"],
		setup(r) {
			const a = he();
			function i(s) {
				return s.to ? a.path === s.to || a.path.startsWith(s.to + "/") : !1;
			}
			function d(s) {
				return i(s) ? "text-ink-gray-9" : "text-ink-gray-4";
			}
			return (s, m) => {
				const y = Se("RouterLink");
				return (
					P(),
					q("nav", ut, [
						(P(!0),
						q(
							xe,
							null,
							Ue(
								R(st),
								(_) => (
									P(),
									q(
										xe,
										{ key: _.label },
										[
											_.to
												? (P(),
												  ce(
														y,
														{
															key: 0,
															to: _.to,
															class: de([ke, d(_)]),
														},
														{
															default: Q(() => [
																N(
																	R(me),
																	{
																		name: _.icon,
																		class: "h-[18px] w-[18px]",
																	},
																	null,
																	8,
																	["name"],
																),
																V(
																	"span",
																	{
																		class: de([
																			"text-[10px]",
																			i(_) &&
																				"font-semibold",
																		]),
																	},
																	pe(_.label),
																	3,
																),
															]),
															_: 2,
														},
														1032,
														["to", "class"],
												  ))
												: (P(),
												  q(
														"button",
														{
															key: 1,
															type: "button",
															class: de([ke, d(_)]),
															onClick: (b) => s.$emit(_.action),
														},
														[
															N(
																R(me),
																{
																	name: _.icon,
																	class: "h-[18px] w-[18px]",
																},
																null,
																8,
																["name"],
															),
															V("span", lt, pe(_.label), 1),
														],
														10,
														ct,
												  )),
										],
										64,
									)
								),
							),
							128,
						)),
					])
				);
			};
		},
	};
var Le = { exports: {} };
(function (r, a) {
	(function (i, d) {
		r.exports = d();
	})(Ee, function () {
		var i = 1e3,
			d = 6e4,
			s = 36e5,
			m = "millisecond",
			y = "second",
			_ = "minute",
			b = "hour",
			p = "day",
			T = "week",
			D = "month",
			H = "quarter",
			C = "year",
			I = "date",
			j = "Invalid Date",
			z =
				/^(\d{4})[-/]?(\d{1,2})?[-/]?(\d{0,2})[Tt\s]*(\d{1,2})?:?(\d{1,2})?:?(\d{1,2})?[.:]?(\d+)?$/,
			W =
				/\[([^\]]+)]|YYYY|YY|M{1,4}|D{1,2}|d{1,4}|H{1,2}|h{1,2}|a|A|m{1,2}|s{1,2}|Z{1,2}|SSS/g,
			J = {
				name: "en",
				weekdays: "Sunday_Monday_Tuesday_Wednesday_Thursday_Friday_Saturday".split("_"),
				months: "January_February_March_April_May_June_July_August_September_October_November_December".split(
					"_",
				),
				ordinal: function (u) {
					var n = ["th", "st", "nd", "rd"],
						e = u % 100;
					return "[" + u + (n[(e - 20) % 10] || n[e] || n[0]) + "]";
				},
			},
			f = function (u, n, e) {
				var o = String(u);
				return !o || o.length >= n ? u : "" + Array(n + 1 - o.length).join(e) + u;
			},
			g = {
				s: f,
				z: function (u) {
					var n = -u.utcOffset(),
						e = Math.abs(n),
						o = Math.floor(e / 60),
						t = e % 60;
					return (n <= 0 ? "+" : "-") + f(o, 2, "0") + ":" + f(t, 2, "0");
				},
				m: function u(n, e) {
					if (n.date() < e.date()) return -u(e, n);
					var o = 12 * (e.year() - n.year()) + (e.month() - n.month()),
						t = n.clone().add(o, D),
						c = e - t < 0,
						l = n.clone().add(o + (c ? -1 : 1), D);
					return +(-(o + (e - t) / (c ? t - l : l - t)) || 0);
				},
				a: function (u) {
					return u < 0 ? Math.ceil(u) || 0 : Math.floor(u);
				},
				p: function (u) {
					return (
						{ M: D, y: C, w: T, d: p, D: I, h: b, m: _, s: y, ms: m, Q: H }[u] ||
						String(u || "")
							.toLowerCase()
							.replace(/s$/, "")
					);
				},
				u: function (u) {
					return u === void 0;
				},
			},
			$ = "en",
			M = {};
		M[$] = J;
		var F = "$isDayjsObject",
			K = function (u) {
				return u instanceof ie || !(!u || !u[F]);
			},
			ae = function u(n, e, o) {
				var t;
				if (!n) return $;
				if (typeof n == "string") {
					var c = n.toLowerCase();
					M[c] && (t = c), e && ((M[c] = e), (t = c));
					var l = n.split("-");
					if (!t && l.length > 1) return u(l[0]);
				} else {
					var v = n.name;
					(M[v] = n), (t = v);
				}
				return !o && t && ($ = t), t || (!o && $);
			},
			w = function (u, n) {
				if (K(u)) return u.clone();
				var e = typeof n == "object" ? n : {};
				return (e.date = u), (e.args = arguments), new ie(e);
			},
			h = g;
		(h.l = ae),
			(h.i = K),
			(h.w = function (u, n) {
				return w(u, { locale: n.$L, utc: n.$u, x: n.$x, $offset: n.$offset });
			});
		var ie = (function () {
				function u(e) {
					(this.$L = ae(e.locale, null, !0)),
						this.parse(e),
						(this.$x = this.$x || e.x || {}),
						(this[F] = !0);
				}
				var n = u.prototype;
				return (
					(n.parse = function (e) {
						(this.$d = (function (o) {
							var t = o.date,
								c = o.utc;
							if (t === null) return new Date(NaN);
							if (h.u(t)) return new Date();
							if (t instanceof Date) return new Date(t);
							if (typeof t == "string" && !/Z$/i.test(t)) {
								var l = t.match(z);
								if (l) {
									var v = l[2] - 1 || 0,
										x = (l[7] || "0").substring(0, 3);
									return c
										? new Date(
												Date.UTC(
													l[1],
													v,
													l[3] || 1,
													l[4] || 0,
													l[5] || 0,
													l[6] || 0,
													x,
												),
										  )
										: new Date(
												l[1],
												v,
												l[3] || 1,
												l[4] || 0,
												l[5] || 0,
												l[6] || 0,
												x,
										  );
								}
							}
							return new Date(t);
						})(e)),
							this.init();
					}),
					(n.init = function () {
						var e = this.$d;
						(this.$y = e.getFullYear()),
							(this.$M = e.getMonth()),
							(this.$D = e.getDate()),
							(this.$W = e.getDay()),
							(this.$H = e.getHours()),
							(this.$m = e.getMinutes()),
							(this.$s = e.getSeconds()),
							(this.$ms = e.getMilliseconds());
					}),
					(n.$utils = function () {
						return h;
					}),
					(n.isValid = function () {
						return this.$d.toString() !== j;
					}),
					(n.isSame = function (e, o) {
						var t = w(e);
						return this.startOf(o) <= t && t <= this.endOf(o);
					}),
					(n.isAfter = function (e, o) {
						return w(e) < this.startOf(o);
					}),
					(n.isBefore = function (e, o) {
						return this.endOf(o) < w(e);
					}),
					(n.$g = function (e, o, t) {
						return h.u(e) ? this[o] : this.set(t, e);
					}),
					(n.unix = function () {
						return Math.floor(this.valueOf() / 1e3);
					}),
					(n.valueOf = function () {
						return this.$d.getTime();
					}),
					(n.startOf = function (e, o) {
						var t = this,
							c = !!h.u(o) || o,
							l = h.p(e),
							v = function (G, L) {
								var U = h.w(t.$u ? Date.UTC(t.$y, L, G) : new Date(t.$y, L, G), t);
								return c ? U : U.endOf(p);
							},
							x = function (G, L) {
								return h.w(
									t
										.toDate()
										[G].apply(
											t.toDate("s"),
											(c ? [0, 0, 0, 0] : [23, 59, 59, 999]).slice(L),
										),
									t,
								);
							},
							k = this.$W,
							E = this.$M,
							Y = this.$D,
							ee = "set" + (this.$u ? "UTC" : "");
						switch (l) {
							case C:
								return c ? v(1, 0) : v(31, 11);
							case D:
								return c ? v(1, E) : v(0, E + 1);
							case T:
								var Z = this.$locale().weekStart || 0,
									se = (k < Z ? k + 7 : k) - Z;
								return v(c ? Y - se : Y + (6 - se), E);
							case p:
							case I:
								return x(ee + "Hours", 0);
							case b:
								return x(ee + "Minutes", 1);
							case _:
								return x(ee + "Seconds", 2);
							case y:
								return x(ee + "Milliseconds", 3);
							default:
								return this.clone();
						}
					}),
					(n.endOf = function (e) {
						return this.startOf(e, !1);
					}),
					(n.$set = function (e, o) {
						var t,
							c = h.p(e),
							l = "set" + (this.$u ? "UTC" : ""),
							v = ((t = {}),
							(t[p] = l + "Date"),
							(t[I] = l + "Date"),
							(t[D] = l + "Month"),
							(t[C] = l + "FullYear"),
							(t[b] = l + "Hours"),
							(t[_] = l + "Minutes"),
							(t[y] = l + "Seconds"),
							(t[m] = l + "Milliseconds"),
							t)[c],
							x = c === p ? this.$D + (o - this.$W) : o;
						if (c === D || c === C) {
							var k = this.clone().set(I, 1);
							k.$d[v](x),
								k.init(),
								(this.$d = k.set(I, Math.min(this.$D, k.daysInMonth())).$d);
						} else v && this.$d[v](x);
						return this.init(), this;
					}),
					(n.set = function (e, o) {
						return this.clone().$set(e, o);
					}),
					(n.get = function (e) {
						return this[h.p(e)]();
					}),
					(n.add = function (e, o) {
						var t,
							c = this;
						e = Number(e);
						var l = h.p(o),
							v = function (E) {
								var Y = w(c);
								return h.w(Y.date(Y.date() + Math.round(E * e)), c);
							};
						if (l === D) return this.set(D, this.$M + e);
						if (l === C) return this.set(C, this.$y + e);
						if (l === p) return v(1);
						if (l === T) return v(7);
						var x = ((t = {}), (t[_] = d), (t[b] = s), (t[y] = i), t)[l] || 1,
							k = this.$d.getTime() + e * x;
						return h.w(k, this);
					}),
					(n.subtract = function (e, o) {
						return this.add(-1 * e, o);
					}),
					(n.format = function (e) {
						var o = this,
							t = this.$locale();
						if (!this.isValid()) return t.invalidDate || j;
						var c = e || "YYYY-MM-DDTHH:mm:ssZ",
							l = h.z(this),
							v = this.$H,
							x = this.$m,
							k = this.$M,
							E = t.weekdays,
							Y = t.months,
							ee = t.meridiem,
							Z = function (L, U, oe, ue) {
								return (L && (L[U] || L(o, c))) || oe[U].slice(0, ue);
							},
							se = function (L) {
								return h.s(v % 12 || 12, L, "0");
							},
							G =
								ee ||
								function (L, U, oe) {
									var ue = L < 12 ? "AM" : "PM";
									return oe ? ue.toLowerCase() : ue;
								};
						return c.replace(W, function (L, U) {
							return (
								U ||
								(function (oe) {
									switch (oe) {
										case "YY":
											return String(o.$y).slice(-2);
										case "YYYY":
											return h.s(o.$y, 4, "0");
										case "M":
											return k + 1;
										case "MM":
											return h.s(k + 1, 2, "0");
										case "MMM":
											return Z(t.monthsShort, k, Y, 3);
										case "MMMM":
											return Z(Y, k);
										case "D":
											return o.$D;
										case "DD":
											return h.s(o.$D, 2, "0");
										case "d":
											return String(o.$W);
										case "dd":
											return Z(t.weekdaysMin, o.$W, E, 2);
										case "ddd":
											return Z(t.weekdaysShort, o.$W, E, 3);
										case "dddd":
											return E[o.$W];
										case "H":
											return String(v);
										case "HH":
											return h.s(v, 2, "0");
										case "h":
											return se(1);
										case "hh":
											return se(2);
										case "a":
											return G(v, x, !0);
										case "A":
											return G(v, x, !1);
										case "m":
											return String(x);
										case "mm":
											return h.s(x, 2, "0");
										case "s":
											return String(o.$s);
										case "ss":
											return h.s(o.$s, 2, "0");
										case "SSS":
											return h.s(o.$ms, 3, "0");
										case "Z":
											return l;
									}
									return null;
								})(L) ||
								l.replace(":", "")
							);
						});
					}),
					(n.utcOffset = function () {
						return 15 * -Math.round(this.$d.getTimezoneOffset() / 15);
					}),
					(n.diff = function (e, o, t) {
						var c,
							l = this,
							v = h.p(o),
							x = w(e),
							k = (x.utcOffset() - this.utcOffset()) * d,
							E = this - x,
							Y = function () {
								return h.m(l, x);
							};
						switch (v) {
							case C:
								c = Y() / 12;
								break;
							case D:
								c = Y();
								break;
							case H:
								c = Y() / 3;
								break;
							case T:
								c = (E - k) / 6048e5;
								break;
							case p:
								c = (E - k) / 864e5;
								break;
							case b:
								c = E / s;
								break;
							case _:
								c = E / d;
								break;
							case y:
								c = E / i;
								break;
							default:
								c = E;
						}
						return t ? c : h.a(c);
					}),
					(n.daysInMonth = function () {
						return this.endOf(D).$D;
					}),
					(n.$locale = function () {
						return M[this.$L];
					}),
					(n.locale = function (e, o) {
						if (!e) return this.$L;
						var t = this.clone(),
							c = ae(e, o, !0);
						return c && (t.$L = c), t;
					}),
					(n.clone = function () {
						return h.w(this.$d, this);
					}),
					(n.toDate = function () {
						return new Date(this.valueOf());
					}),
					(n.toJSON = function () {
						return this.isValid() ? this.toISOString() : null;
					}),
					(n.toISOString = function () {
						return this.$d.toISOString();
					}),
					(n.toString = function () {
						return this.$d.toUTCString();
					}),
					u
				);
			})(),
			ye = ie.prototype;
		return (
			(w.prototype = ye),
			[
				["$ms", m],
				["$s", y],
				["$m", _],
				["$H", b],
				["$W", p],
				["$M", D],
				["$y", C],
				["$D", I],
			].forEach(function (u) {
				ye[u[1]] = function (n) {
					return this.$g(n, u[0], u[1]);
				};
			}),
			(w.extend = function (u, n) {
				return u.$i || (u(n, ie, w), (u.$i = !0)), w;
			}),
			(w.locale = ae),
			(w.isDayjs = K),
			(w.unix = function (u) {
				return w(1e3 * u);
			}),
			(w.en = M[$]),
			(w.Ls = M),
			(w.p = {}),
			w
		);
	});
})(Le);
var ft = Le.exports;
const X = Te(ft);
var Ae = { exports: {} };
(function (r, a) {
	(function (i, d) {
		r.exports = d();
	})(Ee, function () {
		return function (i, d, s) {
			i = i || {};
			var m = d.prototype,
				y = {
					future: "in %s",
					past: "%s ago",
					s: "a few seconds",
					m: "a minute",
					mm: "%d minutes",
					h: "an hour",
					hh: "%d hours",
					d: "a day",
					dd: "%d days",
					M: "a month",
					MM: "%d months",
					y: "a year",
					yy: "%d years",
				};
			function _(p, T, D, H) {
				return m.fromToBase(p, T, D, H);
			}
			(s.en.relativeTime = y),
				(m.fromToBase = function (p, T, D, H, C) {
					for (
						var I,
							j,
							z,
							W = D.$locale().relativeTime || y,
							J = i.thresholds || [
								{ l: "s", r: 44, d: "second" },
								{ l: "m", r: 89 },
								{ l: "mm", r: 44, d: "minute" },
								{ l: "h", r: 89 },
								{ l: "hh", r: 21, d: "hour" },
								{ l: "d", r: 35 },
								{ l: "dd", r: 25, d: "day" },
								{ l: "M", r: 45 },
								{ l: "MM", r: 10, d: "month" },
								{ l: "y", r: 17 },
								{ l: "yy", d: "year" },
							],
							f = J.length,
							g = 0;
						g < f;
						g += 1
					) {
						var $ = J[g];
						$.d && (I = H ? s(p).diff(D, $.d, !0) : D.diff(p, $.d, !0));
						var M = (i.rounding || Math.round)(Math.abs(I));
						if (((z = I > 0), M <= $.r || !$.r)) {
							M <= 1 && g > 0 && ($ = J[g - 1]);
							var F = W[$.l];
							C && (M = C("" + M)),
								(j = typeof F == "string" ? F.replace("%d", M) : F(M, T, $.l, z));
							break;
						}
					}
					if (T) return j;
					var K = z ? W.future : W.past;
					return typeof K == "function" ? K(j) : K.replace("%s", j);
				}),
				(m.to = function (p, T) {
					return _(p, T, this, !0);
				}),
				(m.from = function (p, T) {
					return _(p, T, this);
				});
			var b = function (p) {
				return p.$u ? s.utc() : s();
			};
			(m.toNow = function (p) {
				return this.to(b(this), p);
			}),
				(m.fromNow = function (p) {
					return this.from(b(this), p);
				});
		};
	});
})(Ae);
var mt = Ae.exports;
const pt = Te(mt);
X.extend(pt);
let Re = "INR";
function ht(r) {
	r && (Re = r);
}
function qt(r, { compact: a = !1, currency: i } = {}) {
	if (r == null || r === "") return "—";
	const d = Number(r);
	if (Number.isNaN(d)) return "—";
	const s = i || Re;
	return new Intl.NumberFormat(s === "INR" ? "en-IN" : "en-US", {
		style: "currency",
		currency: s,
		maximumFractionDigits: a || d % 1 === 0 ? 0 : 2,
	}).format(d);
}
function _t(r, a = "D MMM YYYY") {
	return r ? X(r).format(a) : "—";
}
function zt(r, a) {
	if (!r) return "—";
	if (!a || r === a) return _t(r);
	const i = X(r),
		d = X(a);
	return i.year() === d.year() && i.month() === d.month()
		? `${i.format("D")} to ${d.format("D MMM YYYY")}`
		: `${i.format("D MMM")} to ${d.format("D MMM YYYY")}`;
}
function Jt(r) {
	return r ? X(r).format("HH:mm") : "—";
}
function Kt(r) {
	if (!r) return "00:00:00";
	const a = Math.max(0, X().diff(X(r), "second")),
		i = String(Math.floor(a / 3600)).padStart(2, "0"),
		d = String(Math.floor((a % 3600) / 60)).padStart(2, "0"),
		s = String(a % 60).padStart(2, "0");
	return `${i}:${d}:${s}`;
}
function Zt(r) {
	if (!r || !r.start_time) return null;
	const a = (i) => String(i).slice(0, 5);
	return `${a(r.start_time)} to ${a(r.end_time)}`;
}
const yt = { class: "flex h-[100dvh] overflow-hidden bg-surface-white" },
	vt = { class: "hidden h-full md:block" },
	gt = { class: "flex min-w-0 flex-1 flex-col" },
	$t = { class: "flex-1 overflow-y-auto overflow-x-hidden" },
	xt = { key: 0, class: "p-6" },
	bt = { key: 1, class: "mx-auto max-w-md p-6 text-center" },
	Dt = { class: "mt-2 text-p-base text-ink-gray-6" },
	Mt = { class: "font-medium text-ink-gray-8" },
	wt = { key: 0, class: "fixed inset-y-0 left-0 z-50 md:hidden" },
	kt = {
		__name: "App",
		setup(r) {
			const a = Oe(!1),
				i = he();
			return (
				fe(
					() => i.fullPath,
					() => (a.value = !1),
				),
				fe(
					() => {
						var d;
						return (d = B.data) == null ? void 0 : d.currency;
					},
					(d) => ht(d),
					{ immediate: !0 },
				),
				(d, s) => {
					const m = Se("RouterView");
					return (
						P(),
						ce(R(Je), null, {
							default: Q(() => [
								V("div", yt, [
									V("div", vt, [N(we)]),
									V("div", gt, [
										V("main", $t, [
											R(B).loading && !R(B).data
												? (P(),
												  q("div", xt, [
														N(R(qe), {
															class: "h-5 w-5 text-ink-gray-5",
														}),
												  ]))
												: R(B).data && !R(B).data.employee
												  ? (P(),
												    q("div", bt, [
															s[5] ||
																(s[5] = V(
																	"h1",
																	{
																		class: "text-lg font-semibold text-ink-gray-9",
																	},
																	"No employee record",
																	-1,
																)),
															V("p", Dt, [
																s[3] ||
																	(s[3] = be(
																		" This portal shows your own HR record, and ",
																		-1,
																	)),
																V("span", Mt, pe(R(ne).user), 1),
																s[4] ||
																	(s[4] = be(
																		" is not linked to one yet. Ask HR to set the User field on your Employee record. ",
																		-1,
																	)),
															]),
												    ]))
												  : (P(), ce(m, { key: 2 })),
										]),
										N(dt, {
											class: "md:hidden",
											onMore: s[0] || (s[0] = (y) => (a.value = !0)),
										}),
									]),
									N(
										Me,
										{
											"enter-active-class":
												"transition-opacity duration-150",
											"leave-active-class":
												"transition-opacity duration-150",
											"enter-from-class": "opacity-0",
											"leave-to-class": "opacity-0",
										},
										{
											default: Q(() => [
												a.value
													? (P(),
													  q("div", {
															key: 0,
															class: "fixed inset-0 z-40 bg-black/40 md:hidden",
															onClick:
																s[1] ||
																(s[1] = (y) => (a.value = !1)),
													  }))
													: De("", !0),
											]),
											_: 1,
										},
									),
									N(
										Me,
										{
											"enter-active-class":
												"transition-transform duration-200",
											"leave-active-class":
												"transition-transform duration-200",
											"enter-from-class": "-translate-x-full",
											"leave-to-class": "-translate-x-full",
										},
										{
											default: Q(() => [
												a.value
													? (P(),
													  q("div", wt, [
															N(we, {
																expanded: "",
																onNavigate:
																	s[2] ||
																	(s[2] = (y) => (a.value = !1)),
															}),
													  ]))
													: De("", !0),
											]),
											_: 1,
										},
									),
								]),
								N(R(ze)),
							]),
							_: 1,
						})
					);
				}
			);
		},
	},
	Ot = [
		{ path: "/", redirect: "/home" },
		{
			path: "/home",
			name: "Home",
			component: () =>
				A(
					() => import("./Home-DBGqMnyY.js"),
					__vite__mapDeps([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]),
				),
		},
		{
			path: "/attendance",
			name: "Attendance",
			component: () =>
				A(
					() => import("./Attendance-CLV1kRNW.js"),
					__vite__mapDeps([13, 2, 3, 1, 4, 5, 14, 8, 11, 7, 15, 12]),
				),
		},
		{
			path: "/leave",
			name: "Leave",
			component: () =>
				A(
					() => import("./Leave-59X_GT51.js"),
					__vite__mapDeps([16, 2, 3, 1, 4, 5, 6, 7, 14, 8, 9, 10, 11, 15, 12]),
				),
		},
		{
			path: "/expenses",
			name: "Expenses",
			component: () =>
				A(
					() => import("./Expenses-C-UGZDUr.js"),
					__vite__mapDeps([17, 2, 3, 1, 4, 5, 6, 7, 14, 8, 11, 15, 12]),
				),
		},
		{
			path: "/requests/:type/:name",
			name: "Request",
			component: () =>
				A(
					() => import("./Request-B1_U03dg.js"),
					__vite__mapDeps([18, 2, 3, 1, 4, 5, 6, 7, 14, 8, 11, 15, 12]),
				),
		},
		{ path: "/expenses/:name", redirect: (r) => `/requests/expense/${r.params.name}` },
		{
			path: "/payslips",
			name: "Payslips",
			component: () =>
				A(
					() => import("./Payslips-BPdeU3Bp.js"),
					__vite__mapDeps([19, 2, 3, 1, 4, 5, 6, 7, 14, 8, 11]),
				),
		},
		{
			path: "/payslips/:name",
			name: "Payslip",
			component: () =>
				A(
					() => import("./Payslip-CFlv2Jvw.js"),
					__vite__mapDeps([20, 2, 3, 1, 4, 5, 6, 7, 14, 8, 11]),
				),
		},
		{
			path: "/advances",
			name: "Advances",
			component: () =>
				A(
					() => import("./Advances-D4z4VXmc.js"),
					__vite__mapDeps([21, 2, 3, 1, 4, 6, 7, 14, 8, 15, 12]),
				),
		},
		{
			path: "/directory",
			name: "Directory",
			component: () =>
				A(
					() => import("./Directory-CbMhGYpC.js"),
					__vite__mapDeps([22, 1, 2, 3, 4, 8, 7]),
				),
		},
		{
			path: "/directory/:employee",
			name: "Colleague",
			component: () =>
				A(
					() => import("./Colleague-CM8SqR9s.js"),
					__vite__mapDeps([23, 2, 3, 1, 4, 24, 8, 9]),
				),
		},
		{
			path: "/org-chart",
			name: "OrgChart",
			component: () =>
				A(
					() => import("./OrgChart-B5HV4bG-.js"),
					__vite__mapDeps([25, 2, 3, 1, 4, 11, 7, 26]),
				),
		},
		{
			path: "/holidays",
			name: "Holidays",
			component: () =>
				A(
					() => import("./Holidays-Bk9m_VhS.js"),
					__vite__mapDeps([27, 1, 2, 3, 4, 5, 6, 7, 14, 8, 11]),
				),
		},
		{
			path: "/documents",
			name: "Documents",
			component: () =>
				A(
					() => import("./Documents-B4XK28MO.js"),
					__vite__mapDeps([28, 1, 2, 3, 4, 5, 6, 7, 8]),
				),
		},
		{
			path: "/me",
			name: "Profile",
			component: () =>
				A(
					() => import("./Profile-5WmgxzRt.js"),
					__vite__mapDeps([29, 2, 3, 1, 24, 8, 6, 7, 11, 9, 10, 12]),
				),
		},
		{ path: "/:pathMatch(.*)*", redirect: "/home" },
	],
	_e = Ke({ history: Ze("/hrms"), routes: Ot, scrollBehavior: () => ({ top: 0 }) }),
	re = Ge(kt);
Qe("resourceFetcher", nt);
re.use(Xe);
re.use(_e);
re.component("Button", et);
re.component("FormControl", tt);
re.provide("$session", ne);
_e.beforeEach((r, a, i) =>
	le(void 0, null, function* () {
		if (!ne.isLoggedIn) {
			window.location.href = `/login?redirect-to=${encodeURIComponent(
				"/hrms" + r.fullPath,
			)}`;
			return;
		}
		if (!B.data && !B.loading)
			try {
				yield B.fetch();
			} catch (d) {}
		i();
	}),
);
_e.isReady().then(() =>
	le(void 0, null, function* () {
		re.mount("#app");
	}),
);
export {
	X as a,
	qt as b,
	zt as c,
	_t as d,
	Kt as e,
	Lt as f,
	Rt as g,
	Tt as h,
	It as i,
	Yt as j,
	Pt as k,
	At as l,
	Ut as m,
	Nt as n,
	Ht as o,
	Ct as p,
	Vt as q,
	Bt as r,
	Zt as s,
	Jt as t,
	Wt as u,
	jt as v,
	Ft as w,
};
