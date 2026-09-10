const __vite__mapDeps = (
	i,
	m = __vite__mapDeps,
	d = m.f ||
		(m.f = [
			"assets/Home-C0pHjBgn.js",
			"assets/SectionCard-C5Qs8pBJ.js",
			"assets/frappe-ui-D0k6koYp.js",
			"assets/frappe-ui-Gd3P3Yvw.css",
			"assets/DataTable-BPI_hH2T.js",
			"assets/EmptyState-38_uLDf3.js",
			"assets/DataTable-BCMkhabB.css",
			"assets/StatusBadge-sSVuNJEI.js",
			"assets/PersonRow-2k8WhDWN.js",
			"assets/FieldRow-DoxIhPye.js",
			"assets/toast-BPVivXt-.js",
			"assets/Attendance-DsdvaukV.js",
			"assets/DashGrid-CGnJY6QD.js",
			"assets/StatTiles-CcQndbp7.js",
			"assets/RequestDialog-UMsP4D4j.js",
			"assets/RequestField-CEA0aLLd.js",
			"assets/DateField-DafgtgxX.js",
			"assets/Leave-ByXBDfov.js",
			"assets/BalanceBars-9ROF_iIl.js",
			"assets/Expenses-suXsNGZy.js",
			"assets/TotalRow-DhNOuPhk.js",
			"assets/Request-hIkiCd30.js",
			"assets/Payslips-BO4rJX6X.js",
			"assets/Payslip-_l5-BTWq.js",
			"assets/Advances-tyJB2sdK.js",
			"assets/Directory-CCxFXTcR.js",
			"assets/Colleague-CqZ7kh9t.js",
			"assets/IdentityBand-BZ37_HBf.js",
			"assets/OrgChart-C1AHL9m-.js",
			"assets/Holidays-DQnJRsKu.js",
			"assets/Documents-DN62iRzA.js",
			"assets/Profile-DYVnOsur.js",
			"assets/Extension-Dw3zvxtZ.js",
		]),
) => i.map((i) => d[i]);
var Ie = Object.defineProperty,
	Ye = Object.defineProperties;
var He = Object.getOwnPropertyDescriptors;
var ge = Object.getOwnPropertySymbols;
var Ve = Object.prototype.hasOwnProperty,
	Ne = Object.prototype.propertyIsEnumerable;
var $e = (t, o, i) =>
		o in t
			? Ie(t, o, { enumerable: !0, configurable: !0, writable: !0, value: i })
			: (t[o] = i),
	be = (t, o) => {
		for (var i in o || (o = {})) Ve.call(o, i) && $e(t, i, o[i]);
		if (ge) for (var i of ge(o)) Ne.call(o, i) && $e(t, i, o[i]);
		return t;
	},
	xe = (t, o) => Ye(t, He(o));
var me = (t, o, i) =>
	new Promise((d, s) => {
		var m = (y) => {
				try {
					f(i.next(y));
				} catch (_) {
					s(_);
				}
			},
			h = (y) => {
				try {
					f(i.throw(y));
				} catch (_) {
					s(_);
				}
			},
			f = (y) => (y.done ? d(y.value) : Promise.resolve(y.value).then(m, h));
		f((i = i.apply(t, o)).next());
	});
import {
	c as O,
	r as je,
	a as X,
	u as _e,
	b as Be,
	o as P,
	d as ue,
	w as W,
	e as D,
	t as ce,
	f as V,
	g as A,
	_ as Fe,
	h as B,
	F as ie,
	i as pe,
	j as We,
	k as he,
	l as De,
	m as Ue,
	n as qe,
	p as ze,
	q as Te,
	s as ae,
	v as Me,
	x as Je,
	y as Ke,
	T as we,
	z as ke,
	A as Ze,
	B as Ge,
	C as Qe,
	D as Xe,
	E as et,
	G as tt,
	H as nt,
	I as rt,
	J as st,
	K as ot,
} from "./frappe-ui-D0k6koYp.js";
(function () {
	const o = document.createElement("link").relList;
	if (o && o.supports && o.supports("modulepreload")) return;
	for (const s of document.querySelectorAll('link[rel="modulepreload"]')) d(s);
	new MutationObserver((s) => {
		for (const m of s)
			if (m.type === "childList")
				for (const h of m.addedNodes)
					h.tagName === "LINK" && h.rel === "modulepreload" && d(h);
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
const at = [
		{
			group: "My Work",
			items: [
				{ label: "Home", to: "/home", icon: "lucide-home" },
				{ label: "Attendance", to: "/attendance", icon: "lucide-clock" },
				{ label: "Leave", to: "/leave", icon: "lucide-sunrise" },
				{
					label: "Expenses",
					to: "/expenses",
					icon: "lucide-credit-card",
					countKey: "expenses",
				},
				{ label: "Payslips", to: "/payslips", icon: "lucide-file-text" },
				{ label: "Advances", to: "/advances", icon: "lucide-trending-up" },
			],
		},
		{
			group: "Company",
			items: [
				{ label: "Directory", to: "/directory", icon: "lucide-users" },
				{ label: "Org chart", to: "/org-chart", icon: "lucide-git-merge" },
				{ label: "Holidays", to: "/holidays", icon: "lucide-calendar" },
				{ label: "Documents", to: "/documents", icon: "lucide-folder" },
			],
		},
	],
	it = [
		{ label: "Home", to: "/home", icon: "lucide-home" },
		{ label: "Attendance", to: "/attendance", icon: "lucide-clock" },
		{ label: "Leave", to: "/leave", icon: "lucide-sunrise" },
		{ label: "Pay", to: "/payslips", icon: "lucide-file-text" },
		{ label: "More", action: "more", icon: "lucide-menu" },
	];
function ut() {
	return Object.fromEntries(
		document.cookie
			.split("; ")
			.filter(Boolean)
			.map((t) => {
				const o = t.indexOf("=");
				return [t.slice(0, o), decodeURIComponent(t.slice(o + 1))];
			}),
	);
}
function ct() {
	const t = ut().user_id;
	return t && t !== "Guest" ? t : null;
}
const lt = O({
		url: "logout",
		onSuccess() {
			(ee.user = null), (window.location.href = "/login");
		},
	}),
	ee = je({ user: ct(), isLoggedIn: X(() => !!ee.user), logout: lt }),
	T = (t) => `hrms.api.portal.${t}`,
	j = O({ url: T("get_bootstrap"), cache: "portal:bootstrap" }),
	jt = O({ url: T("get_home") }),
	Bt = O({ url: T("get_attendance") }),
	Ft = O({ url: T("get_leave") }),
	Wt = O({ url: T("get_expenses") }),
	Ut = O({ url: T("get_payslips") }),
	qt = O({ url: T("get_payslip") }),
	zt = O({ url: T("get_advances") }),
	Jt = O({ url: T("get_directory") }),
	Kt = O({ url: T("get_colleague") }),
	Zt = O({ url: T("get_org_chart") }),
	Gt = O({ url: T("get_holidays") }),
	Qt = O({ url: T("get_documents") }),
	Xt = O({ url: T("get_profile") }),
	en = O({ url: T("get_profile_field_options"), cache: "portal:field-options" }),
	tn = O({ url: T("update_profile") }),
	nn = O({ url: T("mark_checkin") }),
	dt = { class: "flex h-12 shrink-0 items-center gap-2 px-3" },
	ft = { class: "min-w-0 leading-tight" },
	mt = { class: "truncate text-sm text-ink-gray-5" },
	pt = { "aria-label": "Portal" },
	ht = { class: "space-y-0.5" },
	_t = { class: "mt-auto px-2 pb-2" },
	Se = {
		__name: "AppSidebar",
		emits: ["navigate"],
		setup(t, { emit: o }) {
			const i = o,
				d = _e(),
				s = Be(),
				m = X(() => {
					var p;
					return (p = j.data) == null ? void 0 : p.employee;
				}),
				h = X(() => {
					var p;
					return ((p = m.value) == null ? void 0 : p.company) || "";
				}),
				f = X(() => {
					var p;
					return ((p = m.value) == null ? void 0 : p.designation) || "Employee";
				}),
				y = X(() => {
					var p;
					return ((p = j.data) == null ? void 0 : p.counts) || {};
				}),
				_ = X(() => {
					var x;
					const p = ((x = j.data) == null ? void 0 : x.extensions) || [];
					return at.map((M) =>
						xe(be({}, M), {
							items: [...M.items, ...p.filter((w) => w.group === M.group)],
						}),
					);
				}),
				E = [
					{
						label: "My Profile",
						icon: "lucide-user",
						onClick: () => {
							s.push("/me"), i("navigate");
						},
					},
					{
						label: "Log Out",
						icon: "lucide-log-out",
						onClick: () => ee.logout.submit(),
					},
				];
			function v(p) {
				return d.path === p || d.path.startsWith(p + "/");
			}
			function N(p) {
				return (p.countKey && y.value[p.countKey]) || 0;
			}
			return (p, x) => (
				P(),
				ue(
					A(ze),
					{ "disable-collapse": "" },
					{
						default: W(() => [
							D("div", dt, [
								x[2] ||
									(x[2] = D(
										"div",
										{
											class: "grid size-7 shrink-0 place-items-center overflow-hidden rounded-4 bg-surface-gray-7 text-xs font-medium text-ink-white",
										},
										" HR ",
										-1,
									)),
								D("div", ft, [
									x[1] ||
										(x[1] = D(
											"div",
											{ class: "truncate text-base text-ink-gray-8" },
											"Frappe HR",
											-1,
										)),
									D("div", mt, ce(h.value), 1),
								]),
							]),
							V(
								A(Fe),
								{ class: "min-h-0 flex-1", "viewport-class": "px-2 pb-4" },
								{
									default: W(() => [
										D("nav", pt, [
											(P(!0),
											B(
												ie,
												null,
												pe(
													_.value,
													(M) => (
														P(),
														B(
															ie,
															{ key: M.group },
															[
																V(
																	A(We),
																	null,
																	{
																		default: W(() => [
																			he(ce(M.group), 1),
																		]),
																		_: 2,
																	},
																	1024,
																),
																D("div", ht, [
																	(P(!0),
																	B(
																		ie,
																		null,
																		pe(
																			M.items,
																			(w) => (
																				P(),
																				ue(
																					A(De),
																					{
																						key: w.to,
																						label: w.label,
																						icon: w.icon,
																						to: w.to,
																						active: v(
																							w.to,
																						),
																						suffix: N(
																							w,
																						)
																							? String(
																									N(
																										w,
																									),
																							  )
																							: void 0,
																						onClick:
																							x[0] ||
																							(x[0] =
																								(
																									F,
																								) =>
																									p.$emit(
																										"navigate",
																									)),
																					},
																					null,
																					8,
																					[
																						"label",
																						"icon",
																						"to",
																						"active",
																						"suffix",
																					],
																				)
																			),
																		),
																		128,
																	)),
																]),
															],
															64,
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
							D("div", _t, [
								V(
									A(Ue),
									{ options: E, "match-trigger-width": "", placement: "top" },
									{
										default: W(() => {
											var M;
											return [
												V(
													A(De),
													{
														label:
															((M = m.value) == null
																? void 0
																: M.employee_name) || "—",
														suffix: f.value,
													},
													{
														prefix: W(() => {
															var w, F;
															return [
																V(
																	A(qe),
																	{
																		label:
																			(w = m.value) == null
																				? void 0
																				: w.employee_name,
																		image:
																			(F = m.value) == null
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
								),
							]),
						]),
						_: 1,
					},
				)
			);
		},
	},
	yt = {
		class: "grid shrink-0 grid-cols-5 border-t border-outline-gray-1 bg-surface-base pb-safe-bottom",
		"aria-label": "Sections",
	},
	vt = ["onClick"],
	gt = { class: "text-[10px]" },
	Oe = "flex flex-col items-center gap-0.5 py-2 transition-colors",
	$t = {
		__name: "BottomTabs",
		emits: ["more"],
		setup(t) {
			const o = _e();
			function i(s) {
				return s.to ? o.path === s.to || o.path.startsWith(s.to + "/") : !1;
			}
			function d(s) {
				return i(s) ? "text-ink-gray-9" : "text-ink-gray-4";
			}
			return (s, m) => {
				const h = Te("RouterLink");
				return (
					P(),
					B("nav", yt, [
						(P(!0),
						B(
							ie,
							null,
							pe(
								A(it),
								(f) => (
									P(),
									B(
										ie,
										{ key: f.label },
										[
											f.to
												? (P(),
												  ue(
														h,
														{
															key: 0,
															to: f.to,
															class: ae([Oe, d(f)]),
														},
														{
															default: W(() => [
																D(
																	"span",
																	{
																		class: ae([
																			f.icon,
																			"h-[18px] w-[18px]",
																		]),
																		"aria-hidden": "true",
																	},
																	null,
																	2,
																),
																D(
																	"span",
																	{
																		class: ae([
																			"text-[10px]",
																			i(f) &&
																				"font-semibold",
																		]),
																	},
																	ce(f.label),
																	3,
																),
															]),
															_: 2,
														},
														1032,
														["to", "class"],
												  ))
												: (P(),
												  B(
														"button",
														{
															key: 1,
															type: "button",
															class: ae([Oe, d(f)]),
															onClick: (y) => s.$emit(f.action),
														},
														[
															D(
																"span",
																{
																	class: ae([
																		f.icon,
																		"h-[18px] w-[18px]",
																	]),
																	"aria-hidden": "true",
																},
																null,
																2,
															),
															D("span", gt, ce(f.label), 1),
														],
														10,
														vt,
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
var Le =
	typeof globalThis != "undefined"
		? globalThis
		: typeof window != "undefined"
		  ? window
		  : typeof global != "undefined"
		    ? global
		    : typeof self != "undefined"
		      ? self
		      : {};
function Ae(t) {
	return t && t.__esModule && Object.prototype.hasOwnProperty.call(t, "default") ? t.default : t;
}
var Pe = { exports: {} };
(function (t, o) {
	(function (i, d) {
		t.exports = d();
	})(Le, function () {
		var i = 1e3,
			d = 6e4,
			s = 36e5,
			m = "millisecond",
			h = "second",
			f = "minute",
			y = "hour",
			_ = "day",
			E = "week",
			v = "month",
			N = "quarter",
			p = "year",
			x = "date",
			M = "Invalid Date",
			w =
				/^(\d{4})[-/]?(\d{1,2})?[-/]?(\d{0,2})[Tt\s]*(\d{1,2})?:?(\d{1,2})?:?(\d{1,2})?[.:]?(\d+)?$/,
			F =
				/\[([^\]]+)]|YYYY|YY|M{1,4}|D{1,2}|d{1,4}|H{1,2}|h{1,2}|a|A|m{1,2}|s{1,2}|Z{1,2}|SSS/g,
			ne = {
				name: "en",
				weekdays: "Sunday_Monday_Tuesday_Wednesday_Thursday_Friday_Saturday".split("_"),
				months: "January_February_March_April_May_June_July_August_September_October_November_December".split(
					"_",
				),
				ordinal: function (u) {
					var r = ["th", "st", "nd", "rd"],
						e = u % 100;
					return "[" + u + (r[(e - 20) % 10] || r[e] || r[0]) + "]";
				},
			},
			re = function (u, r, e) {
				var a = String(u);
				return !a || a.length >= r ? u : "" + Array(r + 1 - a.length).join(e) + u;
			},
			q = {
				s: re,
				z: function (u) {
					var r = -u.utcOffset(),
						e = Math.abs(r),
						a = Math.floor(e / 60),
						n = e % 60;
					return (r <= 0 ? "+" : "-") + re(a, 2, "0") + ":" + re(n, 2, "0");
				},
				m: function u(r, e) {
					if (r.date() < e.date()) return -u(e, r);
					var a = 12 * (e.year() - r.year()) + (e.month() - r.month()),
						n = r.clone().add(a, v),
						c = e - n < 0,
						l = r.clone().add(a + (c ? -1 : 1), v);
					return +(-(a + (e - n) / (c ? n - l : l - n)) || 0);
				},
				a: function (u) {
					return u < 0 ? Math.ceil(u) || 0 : Math.floor(u);
				},
				p: function (u) {
					return (
						{ M: v, y: p, w: E, d: _, D: x, h: y, m: f, s: h, ms: m, Q: N }[u] ||
						String(u || "")
							.toLowerCase()
							.replace(/s$/, "")
					);
				},
				u: function (u) {
					return u === void 0;
				},
			},
			C = "en",
			I = {};
		I[C] = ne;
		var G = "$isDayjsObject",
			z = function (u) {
				return u instanceof de || !(!u || !u[G]);
			},
			le = function u(r, e, a) {
				var n;
				if (!r) return C;
				if (typeof r == "string") {
					var c = r.toLowerCase();
					I[c] && (n = c), e && ((I[c] = e), (n = c));
					var l = r.split("-");
					if (!n && l.length > 1) return u(l[0]);
				} else {
					var $ = r.name;
					(I[$] = r), (n = $);
				}
				return !a && n && (C = n), n || (!a && C);
			},
			k = function (u, r) {
				if (z(u)) return u.clone();
				var e = typeof r == "object" ? r : {};
				return (e.date = u), (e.args = arguments), new de(e);
			},
			g = q;
		(g.l = le),
			(g.i = z),
			(g.w = function (u, r) {
				return k(u, { locale: r.$L, utc: r.$u, x: r.$x, $offset: r.$offset });
			});
		var de = (function () {
				function u(e) {
					(this.$L = le(e.locale, null, !0)),
						this.parse(e),
						(this.$x = this.$x || e.x || {}),
						(this[G] = !0);
				}
				var r = u.prototype;
				return (
					(r.parse = function (e) {
						(this.$d = (function (a) {
							var n = a.date,
								c = a.utc;
							if (n === null) return new Date(NaN);
							if (g.u(n)) return new Date();
							if (n instanceof Date) return new Date(n);
							if (typeof n == "string" && !/Z$/i.test(n)) {
								var l = n.match(w);
								if (l) {
									var $ = l[2] - 1 || 0,
										b = (l[7] || "0").substring(0, 3);
									return c
										? new Date(
												Date.UTC(
													l[1],
													$,
													l[3] || 1,
													l[4] || 0,
													l[5] || 0,
													l[6] || 0,
													b,
												),
										  )
										: new Date(
												l[1],
												$,
												l[3] || 1,
												l[4] || 0,
												l[5] || 0,
												l[6] || 0,
												b,
										  );
								}
							}
							return new Date(n);
						})(e)),
							this.init();
					}),
					(r.init = function () {
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
					(r.$utils = function () {
						return g;
					}),
					(r.isValid = function () {
						return this.$d.toString() !== M;
					}),
					(r.isSame = function (e, a) {
						var n = k(e);
						return this.startOf(a) <= n && n <= this.endOf(a);
					}),
					(r.isAfter = function (e, a) {
						return k(e) < this.startOf(a);
					}),
					(r.isBefore = function (e, a) {
						return this.endOf(a) < k(e);
					}),
					(r.$g = function (e, a, n) {
						return g.u(e) ? this[a] : this.set(n, e);
					}),
					(r.unix = function () {
						return Math.floor(this.valueOf() / 1e3);
					}),
					(r.valueOf = function () {
						return this.$d.getTime();
					}),
					(r.startOf = function (e, a) {
						var n = this,
							c = !!g.u(a) || a,
							l = g.p(e),
							$ = function (K, Y) {
								var U = g.w(n.$u ? Date.UTC(n.$y, Y, K) : new Date(n.$y, Y, K), n);
								return c ? U : U.endOf(_);
							},
							b = function (K, Y) {
								return g.w(
									n
										.toDate()
										[K].apply(
											n.toDate("s"),
											(c ? [0, 0, 0, 0] : [23, 59, 59, 999]).slice(Y),
										),
									n,
								);
							},
							S = this.$W,
							L = this.$M,
							H = this.$D,
							Q = "set" + (this.$u ? "UTC" : "");
						switch (l) {
							case p:
								return c ? $(1, 0) : $(31, 11);
							case v:
								return c ? $(1, L) : $(0, L + 1);
							case E:
								var J = this.$locale().weekStart || 0,
									se = (S < J ? S + 7 : S) - J;
								return $(c ? H - se : H + (6 - se), L);
							case _:
							case x:
								return b(Q + "Hours", 0);
							case y:
								return b(Q + "Minutes", 1);
							case f:
								return b(Q + "Seconds", 2);
							case h:
								return b(Q + "Milliseconds", 3);
							default:
								return this.clone();
						}
					}),
					(r.endOf = function (e) {
						return this.startOf(e, !1);
					}),
					(r.$set = function (e, a) {
						var n,
							c = g.p(e),
							l = "set" + (this.$u ? "UTC" : ""),
							$ = ((n = {}),
							(n[_] = l + "Date"),
							(n[x] = l + "Date"),
							(n[v] = l + "Month"),
							(n[p] = l + "FullYear"),
							(n[y] = l + "Hours"),
							(n[f] = l + "Minutes"),
							(n[h] = l + "Seconds"),
							(n[m] = l + "Milliseconds"),
							n)[c],
							b = c === _ ? this.$D + (a - this.$W) : a;
						if (c === v || c === p) {
							var S = this.clone().set(x, 1);
							S.$d[$](b),
								S.init(),
								(this.$d = S.set(x, Math.min(this.$D, S.daysInMonth())).$d);
						} else $ && this.$d[$](b);
						return this.init(), this;
					}),
					(r.set = function (e, a) {
						return this.clone().$set(e, a);
					}),
					(r.get = function (e) {
						return this[g.p(e)]();
					}),
					(r.add = function (e, a) {
						var n,
							c = this;
						e = Number(e);
						var l = g.p(a),
							$ = function (L) {
								var H = k(c);
								return g.w(H.date(H.date() + Math.round(L * e)), c);
							};
						if (l === v) return this.set(v, this.$M + e);
						if (l === p) return this.set(p, this.$y + e);
						if (l === _) return $(1);
						if (l === E) return $(7);
						var b = ((n = {}), (n[f] = d), (n[y] = s), (n[h] = i), n)[l] || 1,
							S = this.$d.getTime() + e * b;
						return g.w(S, this);
					}),
					(r.subtract = function (e, a) {
						return this.add(-1 * e, a);
					}),
					(r.format = function (e) {
						var a = this,
							n = this.$locale();
						if (!this.isValid()) return n.invalidDate || M;
						var c = e || "YYYY-MM-DDTHH:mm:ssZ",
							l = g.z(this),
							$ = this.$H,
							b = this.$m,
							S = this.$M,
							L = n.weekdays,
							H = n.months,
							Q = n.meridiem,
							J = function (Y, U, oe, fe) {
								return (Y && (Y[U] || Y(a, c))) || oe[U].slice(0, fe);
							},
							se = function (Y) {
								return g.s($ % 12 || 12, Y, "0");
							},
							K =
								Q ||
								function (Y, U, oe) {
									var fe = Y < 12 ? "AM" : "PM";
									return oe ? fe.toLowerCase() : fe;
								};
						return c.replace(F, function (Y, U) {
							return (
								U ||
								(function (oe) {
									switch (oe) {
										case "YY":
											return String(a.$y).slice(-2);
										case "YYYY":
											return g.s(a.$y, 4, "0");
										case "M":
											return S + 1;
										case "MM":
											return g.s(S + 1, 2, "0");
										case "MMM":
											return J(n.monthsShort, S, H, 3);
										case "MMMM":
											return J(H, S);
										case "D":
											return a.$D;
										case "DD":
											return g.s(a.$D, 2, "0");
										case "d":
											return String(a.$W);
										case "dd":
											return J(n.weekdaysMin, a.$W, L, 2);
										case "ddd":
											return J(n.weekdaysShort, a.$W, L, 3);
										case "dddd":
											return L[a.$W];
										case "H":
											return String($);
										case "HH":
											return g.s($, 2, "0");
										case "h":
											return se(1);
										case "hh":
											return se(2);
										case "a":
											return K($, b, !0);
										case "A":
											return K($, b, !1);
										case "m":
											return String(b);
										case "mm":
											return g.s(b, 2, "0");
										case "s":
											return String(a.$s);
										case "ss":
											return g.s(a.$s, 2, "0");
										case "SSS":
											return g.s(a.$ms, 3, "0");
										case "Z":
											return l;
									}
									return null;
								})(Y) ||
								l.replace(":", "")
							);
						});
					}),
					(r.utcOffset = function () {
						return 15 * -Math.round(this.$d.getTimezoneOffset() / 15);
					}),
					(r.diff = function (e, a, n) {
						var c,
							l = this,
							$ = g.p(a),
							b = k(e),
							S = (b.utcOffset() - this.utcOffset()) * d,
							L = this - b,
							H = function () {
								return g.m(l, b);
							};
						switch ($) {
							case p:
								c = H() / 12;
								break;
							case v:
								c = H();
								break;
							case N:
								c = H() / 3;
								break;
							case E:
								c = (L - S) / 6048e5;
								break;
							case _:
								c = (L - S) / 864e5;
								break;
							case y:
								c = L / s;
								break;
							case f:
								c = L / d;
								break;
							case h:
								c = L / i;
								break;
							default:
								c = L;
						}
						return n ? c : g.a(c);
					}),
					(r.daysInMonth = function () {
						return this.endOf(v).$D;
					}),
					(r.$locale = function () {
						return I[this.$L];
					}),
					(r.locale = function (e, a) {
						if (!e) return this.$L;
						var n = this.clone(),
							c = le(e, a, !0);
						return c && (n.$L = c), n;
					}),
					(r.clone = function () {
						return g.w(this.$d, this);
					}),
					(r.toDate = function () {
						return new Date(this.valueOf());
					}),
					(r.toJSON = function () {
						return this.isValid() ? this.toISOString() : null;
					}),
					(r.toISOString = function () {
						return this.$d.toISOString();
					}),
					(r.toString = function () {
						return this.$d.toUTCString();
					}),
					u
				);
			})(),
			ve = de.prototype;
		return (
			(k.prototype = ve),
			[
				["$ms", m],
				["$s", h],
				["$m", f],
				["$H", y],
				["$W", _],
				["$M", v],
				["$y", p],
				["$D", x],
			].forEach(function (u) {
				ve[u[1]] = function (r) {
					return this.$g(r, u[0], u[1]);
				};
			}),
			(k.extend = function (u, r) {
				return u.$i || (u(r, de, k), (u.$i = !0)), k;
			}),
			(k.locale = le),
			(k.isDayjs = z),
			(k.unix = function (u) {
				return k(1e3 * u);
			}),
			(k.en = I[C]),
			(k.Ls = I),
			(k.p = {}),
			k
		);
	});
})(Pe);
var bt = Pe.exports;
const Z = Ae(bt);
var Re = { exports: {} };
(function (t, o) {
	(function (i, d) {
		t.exports = d();
	})(Le, function () {
		return function (i, d, s) {
			i = i || {};
			var m = d.prototype,
				h = {
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
			function f(_, E, v, N) {
				return m.fromToBase(_, E, v, N);
			}
			(s.en.relativeTime = h),
				(m.fromToBase = function (_, E, v, N, p) {
					for (
						var x,
							M,
							w,
							F = v.$locale().relativeTime || h,
							ne = i.thresholds || [
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
							re = ne.length,
							q = 0;
						q < re;
						q += 1
					) {
						var C = ne[q];
						C.d && (x = N ? s(_).diff(v, C.d, !0) : v.diff(_, C.d, !0));
						var I = (i.rounding || Math.round)(Math.abs(x));
						if (((w = x > 0), I <= C.r || !C.r)) {
							I <= 1 && q > 0 && (C = ne[q - 1]);
							var G = F[C.l];
							p && (I = p("" + I)),
								(M = typeof G == "string" ? G.replace("%d", I) : G(I, E, C.l, w));
							break;
						}
					}
					if (E) return M;
					var z = w ? F.future : F.past;
					return typeof z == "function" ? z(M) : z.replace("%s", M);
				}),
				(m.to = function (_, E) {
					return f(_, E, this, !0);
				}),
				(m.from = function (_, E) {
					return f(_, E, this);
				});
			var y = function (_) {
				return _.$u ? s.utc() : s();
			};
			(m.toNow = function (_) {
				return this.to(y(this), _);
			}),
				(m.fromNow = function (_) {
					return this.from(y(this), _);
				});
		};
	});
})(Re);
var xt = Re.exports;
const Dt = Ae(xt);
Z.extend(Dt);
let Ce = "INR";
function Mt(t) {
	t && (Ce = t);
}
function rn(t, { compact: o = !1, currency: i } = {}) {
	if (t == null || t === "") return "—";
	const d = Number(t);
	if (Number.isNaN(d)) return "—";
	const s = i || Ce;
	return new Intl.NumberFormat(s === "INR" ? "en-IN" : "en-US", {
		style: "currency",
		currency: s,
		maximumFractionDigits: o || d % 1 === 0 ? 0 : 2,
	}).format(d);
}
function wt(t, o = "D MMM YYYY") {
	return t ? Z(t).format(o) : "—";
}
function sn(t, o) {
	if (!t) return "—";
	if (!o || t === o) return wt(t);
	const i = Z(t),
		d = Z(o);
	return i.year() === d.year() && i.month() === d.month()
		? `${i.format("D")} to ${d.format("D MMM YYYY")}`
		: `${i.format("D MMM")} to ${d.format("D MMM YYYY")}`;
}
function on(t) {
	return t ? Z(t).format("HH:mm") : "—";
}
function an(t) {
	if (!t) return "00:00:00";
	const o = Math.max(0, Z().diff(Z(t), "second")),
		i = String(Math.floor(o / 3600)).padStart(2, "0"),
		d = String(Math.floor((o % 3600) / 60)).padStart(2, "0"),
		s = String(o % 60).padStart(2, "0");
	return `${i}:${d}:${s}`;
}
function un(t) {
	if (!t || !t.start_time) return null;
	const o = (i) => String(i).slice(0, 5);
	return `${o(t.start_time)} to ${o(t.end_time)}`;
}
const kt = { class: "flex h-[100dvh] overflow-hidden bg-surface-base" },
	St = { class: "hidden h-full md:block" },
	Ot = { class: "flex min-w-0 flex-1 flex-col" },
	Et = { class: "flex-1 overflow-y-auto overflow-x-hidden" },
	Tt = { key: 0, class: "p-6" },
	Lt = { key: 1, class: "mx-auto max-w-md p-6 text-center" },
	At = { class: "mt-2 text-p-base text-ink-gray-6" },
	Pt = { class: "font-medium text-ink-gray-8" },
	Rt = { key: 0, class: "fixed inset-y-0 left-0 z-50 md:hidden" },
	Ct = {
		__name: "App",
		setup(t) {
			const o = Ge(!1),
				i = _e();
			return (
				Me(
					() => i.fullPath,
					() => (o.value = !1),
				),
				Me(
					() => {
						var d;
						return (d = j.data) == null ? void 0 : d.currency;
					},
					(d) => Mt(d),
					{ immediate: !0 },
				),
				(d, s) => {
					const m = Te("RouterView");
					return (
						P(),
						ue(A(Je), null, {
							default: W(() => [
								D("div", kt, [
									D("div", St, [V(Se)]),
									D("div", Ot, [
										D("main", Et, [
											A(j).loading && !A(j).data
												? (P(),
												  B("div", Tt, [
														V(A(Ke), {
															class: "h-5 w-5 text-ink-gray-5",
														}),
												  ]))
												: A(j).data && !A(j).data.employee
												  ? (P(),
												    B("div", Lt, [
															s[5] ||
																(s[5] = D(
																	"h1",
																	{
																		class: "text-lg-semibold text-ink-gray-9",
																	},
																	"No employee record",
																	-1,
																)),
															D("p", At, [
																s[3] ||
																	(s[3] = he(
																		" This portal shows your own HR record, and ",
																		-1,
																	)),
																D("span", Pt, ce(A(ee).user), 1),
																s[4] ||
																	(s[4] = he(
																		" is not linked to one yet. Ask HR to set the User field on your Employee record. ",
																		-1,
																	)),
															]),
												    ]))
												  : (P(), ue(m, { key: 2 })),
										]),
										V($t, {
											class: "md:hidden",
											onMore: s[0] || (s[0] = (h) => (o.value = !0)),
										}),
									]),
									V(
										we,
										{
											"enter-active-class":
												"transition-opacity duration-150",
											"leave-active-class":
												"transition-opacity duration-150",
											"enter-from-class": "opacity-0",
											"leave-to-class": "opacity-0",
										},
										{
											default: W(() => [
												o.value
													? (P(),
													  B("div", {
															key: 0,
															class: "fixed inset-0 z-40 bg-black/40 md:hidden",
															onClick:
																s[1] ||
																(s[1] = (h) => (o.value = !1)),
													  }))
													: ke("", !0),
											]),
											_: 1,
										},
									),
									V(
										we,
										{
											"enter-active-class":
												"transition-transform duration-200",
											"leave-active-class":
												"transition-transform duration-200",
											"enter-from-class": "-translate-x-full",
											"leave-to-class": "-translate-x-full",
										},
										{
											default: W(() => [
												o.value
													? (P(),
													  B("div", Rt, [
															V(Se, {
																onNavigate:
																	s[2] ||
																	(s[2] = (h) => (o.value = !1)),
															}),
													  ]))
													: ke("", !0),
											]),
											_: 1,
										},
									),
								]),
								V(A(Ze)),
							]),
							_: 1,
						})
					);
				}
			);
		},
	},
	It = "modulepreload",
	Yt = function (t) {
		return "/assets/hrms/portal/" + t;
	},
	Ee = {},
	R = function (o, i, d) {
		let s = Promise.resolve();
		if (i && i.length > 0) {
			document.getElementsByTagName("link");
			const h = document.querySelector("meta[property=csp-nonce]"),
				f =
					(h == null ? void 0 : h.nonce) ||
					(h == null ? void 0 : h.getAttribute("nonce"));
			s = Promise.allSettled(
				i.map((y) => {
					if (((y = Yt(y)), y in Ee)) return;
					Ee[y] = !0;
					const _ = y.endsWith(".css"),
						E = _ ? '[rel="stylesheet"]' : "";
					if (document.querySelector(`link[href="${y}"]${E}`)) return;
					const v = document.createElement("link");
					if (
						((v.rel = _ ? "stylesheet" : It),
						_ || (v.as = "script"),
						(v.crossOrigin = ""),
						(v.href = y),
						f && v.setAttribute("nonce", f),
						document.head.appendChild(v),
						_)
					)
						return new Promise((N, p) => {
							v.addEventListener("load", N),
								v.addEventListener("error", () =>
									p(new Error(`Unable to preload CSS for ${y}`)),
								);
						});
				}),
			);
		}
		function m(h) {
			const f = new Event("vite:preloadError", { cancelable: !0 });
			if (((f.payload = h), window.dispatchEvent(f), !f.defaultPrevented)) throw h;
		}
		return s.then((h) => {
			for (const f of h || []) f.status === "rejected" && m(f.reason);
			return o().catch(m);
		});
	},
	Ht = [
		{ path: "/", redirect: "/home" },
		{
			path: "/home",
			name: "Home",
			component: () =>
				R(
					() => import("./Home-C0pHjBgn.js"),
					__vite__mapDeps([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]),
				),
		},
		{
			path: "/attendance",
			name: "Attendance",
			component: () =>
				R(
					() => import("./Attendance-DsdvaukV.js"),
					__vite__mapDeps([11, 2, 3, 1, 12, 13, 7, 9, 5, 14, 15, 16, 10]),
				),
		},
		{
			path: "/leave",
			name: "Leave",
			component: () =>
				R(
					() => import("./Leave-ByXBDfov.js"),
					__vite__mapDeps([17, 2, 3, 1, 12, 4, 5, 6, 13, 7, 8, 18, 14, 15, 16, 10]),
				),
		},
		{
			path: "/expenses",
			name: "Expenses",
			component: () =>
				R(
					() => import("./Expenses-suXsNGZy.js"),
					__vite__mapDeps([19, 2, 3, 1, 4, 5, 6, 13, 7, 20, 14, 15, 16, 10]),
				),
		},
		{
			path: "/requests/:type/:name",
			name: "Request",
			component: () =>
				R(
					() => import("./Request-hIkiCd30.js"),
					__vite__mapDeps([21, 2, 3, 1, 12, 4, 5, 6, 13, 7, 9, 14, 15, 16, 10]),
				),
		},
		{ path: "/expenses/:name", redirect: (t) => `/requests/expense/${t.params.name}` },
		{
			path: "/payslips",
			name: "Payslips",
			component: () =>
				R(
					() => import("./Payslips-BO4rJX6X.js"),
					__vite__mapDeps([22, 2, 3, 1, 12, 4, 5, 6, 13, 7, 9, 16, 10]),
				),
		},
		{
			path: "/payslips/:name",
			name: "Payslip",
			component: () =>
				R(
					() => import("./Payslip-_l5-BTWq.js"),
					__vite__mapDeps([23, 2, 3, 1, 12, 4, 5, 6, 13, 7, 9, 20]),
				),
		},
		{
			path: "/advances",
			name: "Advances",
			component: () =>
				R(
					() => import("./Advances-tyJB2sdK.js"),
					__vite__mapDeps([24, 2, 3, 1, 4, 5, 6, 13, 7, 14, 15, 16, 10]),
				),
		},
		{
			path: "/directory",
			name: "Directory",
			component: () =>
				R(() => import("./Directory-CCxFXTcR.js"), __vite__mapDeps([25, 1, 2, 3, 7, 5])),
		},
		{
			path: "/directory/:employee",
			name: "Colleague",
			component: () =>
				R(
					() => import("./Colleague-CqZ7kh9t.js"),
					__vite__mapDeps([26, 2, 3, 1, 27, 7, 8]),
				),
		},
		{
			path: "/org-chart",
			name: "OrgChart",
			component: () =>
				R(() => import("./OrgChart-C1AHL9m-.js"), __vite__mapDeps([28, 2, 3, 1, 5])),
		},
		{
			path: "/holidays",
			name: "Holidays",
			component: () =>
				R(
					() => import("./Holidays-DQnJRsKu.js"),
					__vite__mapDeps([29, 1, 2, 3, 12, 4, 5, 6, 13, 7, 9]),
				),
		},
		{
			path: "/documents",
			name: "Documents",
			component: () =>
				R(
					() => import("./Documents-DN62iRzA.js"),
					__vite__mapDeps([30, 1, 2, 3, 12, 4, 5, 6, 7]),
				),
		},
		{
			path: "/me",
			name: "Profile",
			component: () =>
				R(
					() => import("./Profile-DYVnOsur.js"),
					__vite__mapDeps([31, 2, 3, 1, 27, 7, 4, 5, 6, 9, 8, 18, 10]),
				),
		},
		{
			path: "/x/:slug",
			name: "Extension",
			component: () =>
				R(
					() => import("./Extension-Dw3zvxtZ.js"),
					__vite__mapDeps([32, 2, 3, 1, 13, 7, 4, 5, 6, 9, 20, 15, 16, 10]),
				),
		},
		{ path: "/:pathMatch(.*)*", redirect: "/home" },
	],
	ye = Qe({ history: Xe("/hrms"), routes: Ht, scrollBehavior: () => ({ top: 0 }) }),
	te = et(Ct);
tt("resourceFetcher", ot);
te.use(nt);
te.use(ye);
te.component("Button", rt);
te.component("FormControl", st);
te.provide("$session", ee);
ye.beforeEach((t, o, i) =>
	me(void 0, null, function* () {
		if (!ee.isLoggedIn) {
			window.location.href = `/login?redirect-to=${encodeURIComponent(
				"/hrms" + t.fullPath,
			)}`;
			return;
		}
		if (!j.data && !j.loading)
			try {
				yield j.fetch();
			} catch (d) {}
		i();
	}),
);
ye.isReady().then(() =>
	me(void 0, null, function* () {
		te.mount("#app");
	}),
);
export {
	rn as a,
	sn as b,
	Z as c,
	wt as d,
	an as e,
	Bt as f,
	Wt as g,
	jt as h,
	qt as i,
	zt as j,
	Jt as k,
	Ft as l,
	nn as m,
	Kt as n,
	Zt as o,
	Ut as p,
	Gt as q,
	Qt as r,
	un as s,
	on as t,
	tn as u,
	Xt as v,
	en as w,
};
