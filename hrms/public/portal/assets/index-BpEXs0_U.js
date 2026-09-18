const __vite__mapDeps = (
	i,
	m = __vite__mapDeps,
	d = m.f ||
		(m.f = [
			"assets/Home-BlUsb_74.js",
			"assets/frappe-ui-CXkWuvNK.js",
			"assets/frappe-ui-Gd3P3Yvw.css",
			"assets/SectionCard-BKeIA1B1.js",
			"assets/DataTable-KquPBl5L.js",
			"assets/EmptyState-DhAxAin0.js",
			"assets/DataTable-BCMkhabB.css",
			"assets/StatusBadge-DcMGXIA6.js",
			"assets/PersonRow-BtXbdUjH.js",
			"assets/FieldRow-2cmCHPuL.js",
			"assets/toast-Ca-cKV9o.js",
			"assets/Attendance-BQn40tyw.js",
			"assets/DashGrid-CcXWxztj.js",
			"assets/StatTiles-knaJnTjR.js",
			"assets/RequestDialog-DuFWjain.js",
			"assets/RequestField-B8HqhQXt.js",
			"assets/DateField-BLUeL_2-.js",
			"assets/Leave-ChQtt7Lk.js",
			"assets/Expenses-CQTc1zQ3.js",
			"assets/TotalRow-CVxIYHPR.js",
			"assets/Request-DoyYVLTK.js",
			"assets/Payslips-F3aI3vOI.js",
			"assets/Payslip-BFdUwNvP.js",
			"assets/Advances-C1gOEb44.js",
			"assets/Appraisals-CSn8NeWg.js",
			"assets/Score-Dz0zaDXE.js",
			"assets/Appraisal-BhPEP4AC.js",
			"assets/Directory-Cjc6dUR2.js",
			"assets/Colleague-BqZPReOK.js",
			"assets/IdentityBand-DFaFZaDc.js",
			"assets/OrgChart-ajZIQDO0.js",
			"assets/Holidays-BDD9rzGz.js",
			"assets/Documents-BiXqaXm2.js",
			"assets/Profile-D_m9OkBn.js",
			"assets/Extension-CSwDbGjD.js",
		]),
) => i.map((i) => d[i]);
var Ye = Object.defineProperty,
	Ve = Object.defineProperties;
var He = Object.getOwnPropertyDescriptors;
var $e = Object.getOwnPropertySymbols;
var Ne = Object.prototype.hasOwnProperty,
	je = Object.prototype.propertyIsEnumerable;
var be = (t, o, i) =>
		o in t
			? Ye(t, o, { enumerable: !0, configurable: !0, writable: !0, value: i })
			: (t[o] = i),
	xe = (t, o) => {
		for (var i in o || (o = {})) Ne.call(o, i) && be(t, i, o[i]);
		if ($e) for (var i of $e(o)) je.call(o, i) && be(t, i, o[i]);
		return t;
	},
	De = (t, o) => Ve(t, He(o));
var me = (t, o, i) =>
	new Promise((d, s) => {
		var p = (y) => {
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
			f = (y) => (y.done ? d(y.value) : Promise.resolve(y.value).then(p, h));
		f((i = i.apply(t, o)).next());
	});
import {
	c as M,
	r as Be,
	a as te,
	u as _e,
	b as Fe,
	d as ye,
	o as C,
	e as ue,
	w as q,
	f as H,
	g as S,
	t as ce,
	h as R,
	_ as Ue,
	i as W,
	F as ie,
	j as pe,
	k as We,
	l as he,
	m as Me,
	n as qe,
	p as ze,
	q as Je,
	s as ae,
	v as we,
	x as Ke,
	y as Ze,
	T as ke,
	z as Ee,
	A as Ge,
	B as Qe,
	C as Xe,
	D as et,
	E as tt,
	G as nt,
	H as rt,
	I as st,
	J as ot,
	K as at,
} from "./frappe-ui-CXkWuvNK.js";
(function () {
	const o = document.createElement("link").relList;
	if (o && o.supports && o.supports("modulepreload")) return;
	for (const s of document.querySelectorAll('link[rel="modulepreload"]')) d(s);
	new MutationObserver((s) => {
		for (const p of s)
			if (p.type === "childList")
				for (const h of p.addedNodes)
					h.tagName === "LINK" && h.rel === "modulepreload" && d(h);
	}).observe(document, { childList: !0, subtree: !0 });
	function i(s) {
		const p = {};
		return (
			s.integrity && (p.integrity = s.integrity),
			s.referrerPolicy && (p.referrerPolicy = s.referrerPolicy),
			s.crossOrigin === "use-credentials"
				? (p.credentials = "include")
				: s.crossOrigin === "anonymous"
				  ? (p.credentials = "omit")
				  : (p.credentials = "same-origin"),
			p
		);
	}
	function d(s) {
		if (s.ep) return;
		s.ep = !0;
		const p = i(s);
		fetch(s.href, p);
	}
})();
const Oe = [
		{
			group: "Leave & Attendance",
			items: [
				{ label: "Attendance", to: "/attendance", icon: "lucide-clock" },
				{ label: "Leave", to: "/leave", icon: "lucide-sunrise" },
			],
		},
		{
			group: "Pay",
			items: [
				{ label: "Payslips", to: "/payslips", icon: "lucide-file-text" },
				{
					label: "Expenses",
					to: "/expenses",
					icon: "lucide-credit-card",
					countKey: "expenses",
				},
				{ label: "Advances", to: "/advances", icon: "lucide-trending-up" },
			],
		},
		{
			group: "Performance",
			items: [{ label: "Appraisals", to: "/appraisals", icon: "lucide-award" }],
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
const lt = M({
		url: "logout",
		onSuccess() {
			(ne.user = null), (window.location.href = "/login");
		},
	}),
	ne = Be({ user: ct(), isLoggedIn: te(() => !!ne.user), logout: lt }),
	k = (t) => `hrms.api.portal.${t}`,
	U = M({ url: k("get_bootstrap"), cache: "portal:bootstrap" }),
	Nt = M({ url: k("get_home") }),
	jt = M({ url: k("get_attendance") }),
	Bt = M({ url: k("get_leave") }),
	Ft = M({ url: k("get_expenses") }),
	Ut = M({ url: k("get_payslips") }),
	Wt = M({ url: k("get_payslip") }),
	qt = M({ url: k("get_advances") }),
	zt = M({ url: k("get_appraisals") }),
	Jt = M({ url: k("get_appraisal") }),
	Kt = M({ url: k("get_directory") }),
	Zt = M({ url: k("get_colleague") }),
	Gt = M({ url: k("get_org_chart") }),
	Qt = M({ url: k("get_holidays") }),
	Xt = M({ url: k("get_documents") }),
	en = M({ url: k("get_profile") }),
	tn = M({ url: k("get_profile_field_options"), cache: "portal:field-options" }),
	nn = M({ url: k("update_profile") }),
	rn = M({ url: k("mark_checkin") }),
	dt = { class: "min-w-0 leading-tight" },
	ft = { class: "truncate text-sm text-ink-gray-5" },
	mt = { "aria-label": "Portal" },
	pt = { class: "mb-1 space-y-0.5" },
	ht = { class: "mt-auto px-2 pb-2" },
	Se = {
		__name: "AppSidebar",
		emits: ["navigate"],
		setup(t, { emit: o }) {
			const i = o,
				d = _e(),
				s = Fe(),
				p = te(() => {
					var m;
					return (m = U.data) == null ? void 0 : m.employee;
				}),
				h = te(() => {
					var m;
					return ((m = p.value) == null ? void 0 : m.company) || "";
				}),
				f = te(() => {
					var m;
					return ((m = p.value) == null ? void 0 : m.designation) || "Employee";
				}),
				y = te(() => {
					var m;
					return ((m = U.data) == null ? void 0 : m.counts) || {};
				}),
				_ = te(() => {
					var w;
					const m = ((w = U.data) == null ? void 0 : w.extensions) || [],
						b = Oe.map((D) =>
							De(xe({}, D), {
								items: [...D.items, ...m.filter((F) => F.group === D.group)],
							}),
						),
						B = new Set(Oe.map((D) => D.group)),
						T = [];
					for (const D of m) {
						if (B.has(D.group)) continue;
						let F = T.find((z) => z.group === D.group);
						F || T.push((F = { group: D.group, items: [] })), F.items.push(D);
					}
					return [...b, ...T];
				}),
				L = [
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
						onClick: () => ne.logout.submit(),
					},
				];
			function g(m) {
				return d.path === m || d.path.startsWith(m + "/");
			}
			function j(m) {
				return (m.countKey && y.value[m.countKey]) || 0;
			}
			return (m, b) => {
				const B = ye("RouterLink");
				return (
					C(),
					ue(
						R(Je),
						{ "disable-collapse": "" },
						{
							default: q(() => [
								H(
									B,
									{
										to: "/home",
										"aria-label": "Home",
										class: "flex h-12 shrink-0 items-center gap-2 px-3 transition-colors hover:bg-surface-gray-2",
										onClick: b[0] || (b[0] = (T) => m.$emit("navigate")),
									},
									{
										default: q(() => [
											b[3] ||
												(b[3] = S(
													"div",
													{
														class: "grid size-7 shrink-0 place-items-center overflow-hidden rounded-4 bg-surface-gray-7 text-xs font-medium text-ink-white",
													},
													" HR ",
													-1,
												)),
											S("div", dt, [
												b[2] ||
													(b[2] = S(
														"div",
														{
															class: "truncate text-base text-ink-gray-8",
														},
														"Frappe HR",
														-1,
													)),
												S("div", ft, ce(h.value), 1),
											]),
										]),
										_: 1,
									},
								),
								H(
									R(Ue),
									{ class: "min-h-0 flex-1", "viewport-class": "px-2 pb-4" },
									{
										default: q(() => [
											S("nav", mt, [
												(C(!0),
												W(
													ie,
													null,
													pe(
														_.value,
														(T) => (
															C(),
															W(
																ie,
																{ key: T.group },
																[
																	H(
																		R(We),
																		null,
																		{
																			default: q(() => [
																				he(ce(T.group), 1),
																			]),
																			_: 2,
																		},
																		1024,
																	),
																	S("div", pt, [
																		(C(!0),
																		W(
																			ie,
																			null,
																			pe(
																				T.items,
																				(w) => (
																					C(),
																					ue(
																						R(Me),
																						{
																							key: w.to,
																							label: w.label,
																							icon: w.icon,
																							to: w.to,
																							active: g(
																								w.to,
																							),
																							suffix: j(
																								w,
																							)
																								? String(
																										j(
																											w,
																										),
																								  )
																								: void 0,
																							onClick:
																								b[1] ||
																								(b[1] =
																									(
																										D,
																									) =>
																										m.$emit(
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
								S("div", ht, [
									H(
										R(qe),
										{
											options: L,
											"match-trigger-width": "",
											placement: "top",
										},
										{
											default: q(() => {
												var T;
												return [
													H(
														R(Me),
														{
															label:
																((T = p.value) == null
																	? void 0
																	: T.employee_name) || "—",
															suffix: f.value,
														},
														{
															prefix: q(() => {
																var w, D;
																return [
																	H(
																		R(ze),
																		{
																			label:
																				(w = p.value) ==
																				null
																					? void 0
																					: w.employee_name,
																			image:
																				(D = p.value) ==
																				null
																					? void 0
																					: D.image,
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
			};
		},
	},
	_t = {
		class: "grid shrink-0 grid-cols-5 border-t border-outline-gray-1 bg-surface-base pb-safe-bottom",
		"aria-label": "Sections",
	},
	yt = ["onClick"],
	gt = { class: "text-[10px]" },
	Le = "flex flex-col items-center gap-0.5 py-2 transition-colors",
	vt = {
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
			return (s, p) => {
				const h = ye("RouterLink");
				return (
					C(),
					W("nav", _t, [
						(C(!0),
						W(
							ie,
							null,
							pe(
								R(it),
								(f) => (
									C(),
									W(
										ie,
										{ key: f.label },
										[
											f.to
												? (C(),
												  ue(
														h,
														{
															key: 0,
															to: f.to,
															class: ae([Le, d(f)]),
														},
														{
															default: q(() => [
																S(
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
																S(
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
												: (C(),
												  W(
														"button",
														{
															key: 1,
															type: "button",
															class: ae([Le, d(f)]),
															onClick: (y) => s.$emit(f.action),
														},
														[
															S(
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
															S("span", gt, ce(f.label), 1),
														],
														10,
														yt,
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
var Ae =
	typeof globalThis != "undefined"
		? globalThis
		: typeof window != "undefined"
		  ? window
		  : typeof global != "undefined"
		    ? global
		    : typeof self != "undefined"
		      ? self
		      : {};
function Pe(t) {
	return t && t.__esModule && Object.prototype.hasOwnProperty.call(t, "default") ? t.default : t;
}
var Re = { exports: {} };
(function (t, o) {
	(function (i, d) {
		t.exports = d();
	})(Ae, function () {
		var i = 1e3,
			d = 6e4,
			s = 36e5,
			p = "millisecond",
			h = "second",
			f = "minute",
			y = "hour",
			_ = "day",
			L = "week",
			g = "month",
			j = "quarter",
			m = "year",
			b = "date",
			B = "Invalid Date",
			T =
				/^(\d{4})[-/]?(\d{1,2})?[-/]?(\d{0,2})[Tt\s]*(\d{1,2})?:?(\d{1,2})?:?(\d{1,2})?[.:]?(\d+)?$/,
			w =
				/\[([^\]]+)]|YYYY|YY|M{1,4}|D{1,2}|d{1,4}|H{1,2}|h{1,2}|a|A|m{1,2}|s{1,2}|Z{1,2}|SSS/g,
			D = {
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
			F = function (u, r, e) {
				var a = String(u);
				return !a || a.length >= r ? u : "" + Array(r + 1 - a.length).join(e) + u;
			},
			z = {
				s: F,
				z: function (u) {
					var r = -u.utcOffset(),
						e = Math.abs(r),
						a = Math.floor(e / 60),
						n = e % 60;
					return (r <= 0 ? "+" : "-") + F(a, 2, "0") + ":" + F(n, 2, "0");
				},
				m: function u(r, e) {
					if (r.date() < e.date()) return -u(e, r);
					var a = 12 * (e.year() - r.year()) + (e.month() - r.month()),
						n = r.clone().add(a, g),
						c = e - n < 0,
						l = r.clone().add(a + (c ? -1 : 1), g);
					return +(-(a + (e - n) / (c ? n - l : l - n)) || 0);
				},
				a: function (u) {
					return u < 0 ? Math.ceil(u) || 0 : Math.floor(u);
				},
				p: function (u) {
					return (
						{ M: g, y: m, w: L, d: _, D: b, h: y, m: f, s: h, ms: p, Q: j }[u] ||
						String(u || "")
							.toLowerCase()
							.replace(/s$/, "")
					);
				},
				u: function (u) {
					return u === void 0;
				},
			},
			I = "en",
			Y = {};
		Y[I] = D;
		var X = "$isDayjsObject",
			K = function (u) {
				return u instanceof de || !(!u || !u[X]);
			},
			le = function u(r, e, a) {
				var n;
				if (!r) return I;
				if (typeof r == "string") {
					var c = r.toLowerCase();
					Y[c] && (n = c), e && ((Y[c] = e), (n = c));
					var l = r.split("-");
					if (!n && l.length > 1) return u(l[0]);
				} else {
					var $ = r.name;
					(Y[$] = r), (n = $);
				}
				return !a && n && (I = n), n || (!a && I);
			},
			E = function (u, r) {
				if (K(u)) return u.clone();
				var e = typeof r == "object" ? r : {};
				return (e.date = u), (e.args = arguments), new de(e);
			},
			v = z;
		(v.l = le),
			(v.i = K),
			(v.w = function (u, r) {
				return E(u, { locale: r.$L, utc: r.$u, x: r.$x, $offset: r.$offset });
			});
		var de = (function () {
				function u(e) {
					(this.$L = le(e.locale, null, !0)),
						this.parse(e),
						(this.$x = this.$x || e.x || {}),
						(this[X] = !0);
				}
				var r = u.prototype;
				return (
					(r.parse = function (e) {
						(this.$d = (function (a) {
							var n = a.date,
								c = a.utc;
							if (n === null) return new Date(NaN);
							if (v.u(n)) return new Date();
							if (n instanceof Date) return new Date(n);
							if (typeof n == "string" && !/Z$/i.test(n)) {
								var l = n.match(T);
								if (l) {
									var $ = l[2] - 1 || 0,
										x = (l[7] || "0").substring(0, 3);
									return c
										? new Date(
												Date.UTC(
													l[1],
													$,
													l[3] || 1,
													l[4] || 0,
													l[5] || 0,
													l[6] || 0,
													x,
												),
										  )
										: new Date(
												l[1],
												$,
												l[3] || 1,
												l[4] || 0,
												l[5] || 0,
												l[6] || 0,
												x,
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
						return v;
					}),
					(r.isValid = function () {
						return this.$d.toString() !== B;
					}),
					(r.isSame = function (e, a) {
						var n = E(e);
						return this.startOf(a) <= n && n <= this.endOf(a);
					}),
					(r.isAfter = function (e, a) {
						return E(e) < this.startOf(a);
					}),
					(r.isBefore = function (e, a) {
						return this.endOf(a) < E(e);
					}),
					(r.$g = function (e, a, n) {
						return v.u(e) ? this[a] : this.set(n, e);
					}),
					(r.unix = function () {
						return Math.floor(this.valueOf() / 1e3);
					}),
					(r.valueOf = function () {
						return this.$d.getTime();
					}),
					(r.startOf = function (e, a) {
						var n = this,
							c = !!v.u(a) || a,
							l = v.p(e),
							$ = function (G, V) {
								var J = v.w(n.$u ? Date.UTC(n.$y, V, G) : new Date(n.$y, V, G), n);
								return c ? J : J.endOf(_);
							},
							x = function (G, V) {
								return v.w(
									n
										.toDate()
										[G].apply(
											n.toDate("s"),
											(c ? [0, 0, 0, 0] : [23, 59, 59, 999]).slice(V),
										),
									n,
								);
							},
							O = this.$W,
							P = this.$M,
							N = this.$D,
							ee = "set" + (this.$u ? "UTC" : "");
						switch (l) {
							case m:
								return c ? $(1, 0) : $(31, 11);
							case g:
								return c ? $(1, P) : $(0, P + 1);
							case L:
								var Z = this.$locale().weekStart || 0,
									se = (O < Z ? O + 7 : O) - Z;
								return $(c ? N - se : N + (6 - se), P);
							case _:
							case b:
								return x(ee + "Hours", 0);
							case y:
								return x(ee + "Minutes", 1);
							case f:
								return x(ee + "Seconds", 2);
							case h:
								return x(ee + "Milliseconds", 3);
							default:
								return this.clone();
						}
					}),
					(r.endOf = function (e) {
						return this.startOf(e, !1);
					}),
					(r.$set = function (e, a) {
						var n,
							c = v.p(e),
							l = "set" + (this.$u ? "UTC" : ""),
							$ = ((n = {}),
							(n[_] = l + "Date"),
							(n[b] = l + "Date"),
							(n[g] = l + "Month"),
							(n[m] = l + "FullYear"),
							(n[y] = l + "Hours"),
							(n[f] = l + "Minutes"),
							(n[h] = l + "Seconds"),
							(n[p] = l + "Milliseconds"),
							n)[c],
							x = c === _ ? this.$D + (a - this.$W) : a;
						if (c === g || c === m) {
							var O = this.clone().set(b, 1);
							O.$d[$](x),
								O.init(),
								(this.$d = O.set(b, Math.min(this.$D, O.daysInMonth())).$d);
						} else $ && this.$d[$](x);
						return this.init(), this;
					}),
					(r.set = function (e, a) {
						return this.clone().$set(e, a);
					}),
					(r.get = function (e) {
						return this[v.p(e)]();
					}),
					(r.add = function (e, a) {
						var n,
							c = this;
						e = Number(e);
						var l = v.p(a),
							$ = function (P) {
								var N = E(c);
								return v.w(N.date(N.date() + Math.round(P * e)), c);
							};
						if (l === g) return this.set(g, this.$M + e);
						if (l === m) return this.set(m, this.$y + e);
						if (l === _) return $(1);
						if (l === L) return $(7);
						var x = ((n = {}), (n[f] = d), (n[y] = s), (n[h] = i), n)[l] || 1,
							O = this.$d.getTime() + e * x;
						return v.w(O, this);
					}),
					(r.subtract = function (e, a) {
						return this.add(-1 * e, a);
					}),
					(r.format = function (e) {
						var a = this,
							n = this.$locale();
						if (!this.isValid()) return n.invalidDate || B;
						var c = e || "YYYY-MM-DDTHH:mm:ssZ",
							l = v.z(this),
							$ = this.$H,
							x = this.$m,
							O = this.$M,
							P = n.weekdays,
							N = n.months,
							ee = n.meridiem,
							Z = function (V, J, oe, fe) {
								return (V && (V[J] || V(a, c))) || oe[J].slice(0, fe);
							},
							se = function (V) {
								return v.s($ % 12 || 12, V, "0");
							},
							G =
								ee ||
								function (V, J, oe) {
									var fe = V < 12 ? "AM" : "PM";
									return oe ? fe.toLowerCase() : fe;
								};
						return c.replace(w, function (V, J) {
							return (
								J ||
								(function (oe) {
									switch (oe) {
										case "YY":
											return String(a.$y).slice(-2);
										case "YYYY":
											return v.s(a.$y, 4, "0");
										case "M":
											return O + 1;
										case "MM":
											return v.s(O + 1, 2, "0");
										case "MMM":
											return Z(n.monthsShort, O, N, 3);
										case "MMMM":
											return Z(N, O);
										case "D":
											return a.$D;
										case "DD":
											return v.s(a.$D, 2, "0");
										case "d":
											return String(a.$W);
										case "dd":
											return Z(n.weekdaysMin, a.$W, P, 2);
										case "ddd":
											return Z(n.weekdaysShort, a.$W, P, 3);
										case "dddd":
											return P[a.$W];
										case "H":
											return String($);
										case "HH":
											return v.s($, 2, "0");
										case "h":
											return se(1);
										case "hh":
											return se(2);
										case "a":
											return G($, x, !0);
										case "A":
											return G($, x, !1);
										case "m":
											return String(x);
										case "mm":
											return v.s(x, 2, "0");
										case "s":
											return String(a.$s);
										case "ss":
											return v.s(a.$s, 2, "0");
										case "SSS":
											return v.s(a.$ms, 3, "0");
										case "Z":
											return l;
									}
									return null;
								})(V) ||
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
							$ = v.p(a),
							x = E(e),
							O = (x.utcOffset() - this.utcOffset()) * d,
							P = this - x,
							N = function () {
								return v.m(l, x);
							};
						switch ($) {
							case m:
								c = N() / 12;
								break;
							case g:
								c = N();
								break;
							case j:
								c = N() / 3;
								break;
							case L:
								c = (P - O) / 6048e5;
								break;
							case _:
								c = (P - O) / 864e5;
								break;
							case y:
								c = P / s;
								break;
							case f:
								c = P / d;
								break;
							case h:
								c = P / i;
								break;
							default:
								c = P;
						}
						return n ? c : v.a(c);
					}),
					(r.daysInMonth = function () {
						return this.endOf(g).$D;
					}),
					(r.$locale = function () {
						return Y[this.$L];
					}),
					(r.locale = function (e, a) {
						if (!e) return this.$L;
						var n = this.clone(),
							c = le(e, a, !0);
						return c && (n.$L = c), n;
					}),
					(r.clone = function () {
						return v.w(this.$d, this);
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
			(E.prototype = ve),
			[
				["$ms", p],
				["$s", h],
				["$m", f],
				["$H", y],
				["$W", _],
				["$M", g],
				["$y", m],
				["$D", b],
			].forEach(function (u) {
				ve[u[1]] = function (r) {
					return this.$g(r, u[0], u[1]);
				};
			}),
			(E.extend = function (u, r) {
				return u.$i || (u(r, de, E), (u.$i = !0)), E;
			}),
			(E.locale = le),
			(E.isDayjs = K),
			(E.unix = function (u) {
				return E(1e3 * u);
			}),
			(E.en = Y[I]),
			(E.Ls = Y),
			(E.p = {}),
			E
		);
	});
})(Re);
var $t = Re.exports;
const Q = Pe($t);
var Ce = { exports: {} };
(function (t, o) {
	(function (i, d) {
		t.exports = d();
	})(Ae, function () {
		return function (i, d, s) {
			i = i || {};
			var p = d.prototype,
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
			function f(_, L, g, j) {
				return p.fromToBase(_, L, g, j);
			}
			(s.en.relativeTime = h),
				(p.fromToBase = function (_, L, g, j, m) {
					for (
						var b,
							B,
							T,
							w = g.$locale().relativeTime || h,
							D = i.thresholds || [
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
							F = D.length,
							z = 0;
						z < F;
						z += 1
					) {
						var I = D[z];
						I.d && (b = j ? s(_).diff(g, I.d, !0) : g.diff(_, I.d, !0));
						var Y = (i.rounding || Math.round)(Math.abs(b));
						if (((T = b > 0), Y <= I.r || !I.r)) {
							Y <= 1 && z > 0 && (I = D[z - 1]);
							var X = w[I.l];
							m && (Y = m("" + Y)),
								(B = typeof X == "string" ? X.replace("%d", Y) : X(Y, L, I.l, T));
							break;
						}
					}
					if (L) return B;
					var K = T ? w.future : w.past;
					return typeof K == "function" ? K(B) : K.replace("%s", B);
				}),
				(p.to = function (_, L) {
					return f(_, L, this, !0);
				}),
				(p.from = function (_, L) {
					return f(_, L, this);
				});
			var y = function (_) {
				return _.$u ? s.utc() : s();
			};
			(p.toNow = function (_) {
				return this.to(y(this), _);
			}),
				(p.fromNow = function (_) {
					return this.from(y(this), _);
				});
		};
	});
})(Ce);
var bt = Ce.exports;
const xt = Pe(bt);
Q.extend(xt);
let Ie = "INR";
function Dt(t) {
	t && (Ie = t);
}
function sn(t, { compact: o = !1, currency: i } = {}) {
	if (t == null || t === "") return "—";
	const d = Number(t);
	if (Number.isNaN(d)) return "—";
	const s = i || Ie;
	return new Intl.NumberFormat(s === "INR" ? "en-IN" : "en-US", {
		style: "currency",
		currency: s,
		maximumFractionDigits: o || d % 1 === 0 ? 0 : 2,
	}).format(d);
}
function Mt(t, o = "D MMM YYYY") {
	return t ? Q(t).format(o) : "—";
}
function on(t, o) {
	if (!t) return "—";
	if (!o || t === o) return Mt(t);
	const i = Q(t),
		d = Q(o);
	return i.year() === d.year() && i.month() === d.month()
		? `${i.format("D")} to ${d.format("D MMM YYYY")}`
		: `${i.format("D MMM")} to ${d.format("D MMM YYYY")}`;
}
function an(t) {
	return t ? Q(t).format("HH:mm") : "—";
}
function un(t) {
	if (!t) return "00:00:00";
	const o = Math.max(0, Q().diff(Q(t), "second")),
		i = String(Math.floor(o / 3600)).padStart(2, "0"),
		d = String(Math.floor((o % 3600) / 60)).padStart(2, "0"),
		s = String(o % 60).padStart(2, "0");
	return `${i}:${d}:${s}`;
}
function cn(t) {
	if (!t || !t.start_time) return null;
	const o = (i) => String(i).slice(0, 5);
	return `${o(t.start_time)} to ${o(t.end_time)}`;
}
const wt = { class: "flex h-[100dvh] overflow-hidden bg-surface-base" },
	kt = { class: "hidden h-full md:block" },
	Et = { class: "flex min-w-0 flex-1 flex-col" },
	Ot = { class: "flex-1 overflow-y-auto overflow-x-hidden" },
	St = { key: 0, class: "p-6" },
	Lt = { key: 1, class: "mx-auto max-w-md p-6 text-center" },
	Tt = { class: "mt-2 text-p-base text-ink-gray-6" },
	At = { class: "font-medium text-ink-gray-8" },
	Pt = { key: 0, class: "fixed inset-y-0 left-0 z-50 md:hidden" },
	Rt = {
		__name: "App",
		setup(t) {
			const o = Qe(!1),
				i = _e();
			return (
				we(
					() => i.fullPath,
					() => (o.value = !1),
				),
				we(
					() => {
						var d;
						return (d = U.data) == null ? void 0 : d.currency;
					},
					(d) => Dt(d),
					{ immediate: !0 },
				),
				(d, s) => {
					const p = ye("RouterView");
					return (
						C(),
						ue(R(Ke), null, {
							default: q(() => [
								S("div", wt, [
									S("div", kt, [H(Se)]),
									S("div", Et, [
										S("main", Ot, [
											R(U).loading && !R(U).data
												? (C(),
												  W("div", St, [
														H(R(Ze), {
															class: "h-5 w-5 text-ink-gray-5",
														}),
												  ]))
												: R(U).data && !R(U).data.employee
												  ? (C(),
												    W("div", Lt, [
															s[5] ||
																(s[5] = S(
																	"h1",
																	{
																		class: "text-lg-semibold text-ink-gray-9",
																	},
																	"No employee record",
																	-1,
																)),
															S("p", Tt, [
																s[3] ||
																	(s[3] = he(
																		" This portal shows your own HR record, and ",
																		-1,
																	)),
																S("span", At, ce(R(ne).user), 1),
																s[4] ||
																	(s[4] = he(
																		" is not linked to one yet. Ask HR to set the User field on your Employee record. ",
																		-1,
																	)),
															]),
												    ]))
												  : (C(), ue(p, { key: 2 })),
										]),
										H(vt, {
											class: "md:hidden",
											onMore: s[0] || (s[0] = (h) => (o.value = !0)),
										}),
									]),
									H(
										ke,
										{
											"enter-active-class":
												"transition-opacity duration-150",
											"leave-active-class":
												"transition-opacity duration-150",
											"enter-from-class": "opacity-0",
											"leave-to-class": "opacity-0",
										},
										{
											default: q(() => [
												o.value
													? (C(),
													  W("div", {
															key: 0,
															class: "fixed inset-0 z-40 bg-black/40 md:hidden",
															onClick:
																s[1] ||
																(s[1] = (h) => (o.value = !1)),
													  }))
													: Ee("", !0),
											]),
											_: 1,
										},
									),
									H(
										ke,
										{
											"enter-active-class":
												"transition-transform duration-200",
											"leave-active-class":
												"transition-transform duration-200",
											"enter-from-class": "-translate-x-full",
											"leave-to-class": "-translate-x-full",
										},
										{
											default: q(() => [
												o.value
													? (C(),
													  W("div", Pt, [
															H(Se, {
																onNavigate:
																	s[2] ||
																	(s[2] = (h) => (o.value = !1)),
															}),
													  ]))
													: Ee("", !0),
											]),
											_: 1,
										},
									),
								]),
								H(R(Ge)),
							]),
							_: 1,
						})
					);
				}
			);
		},
	},
	Ct = "modulepreload",
	It = function (t) {
		return "/assets/hrms/portal/" + t;
	},
	Te = {},
	A = function (o, i, d) {
		let s = Promise.resolve();
		if (i && i.length > 0) {
			document.getElementsByTagName("link");
			const h = document.querySelector("meta[property=csp-nonce]"),
				f =
					(h == null ? void 0 : h.nonce) ||
					(h == null ? void 0 : h.getAttribute("nonce"));
			s = Promise.allSettled(
				i.map((y) => {
					if (((y = It(y)), y in Te)) return;
					Te[y] = !0;
					const _ = y.endsWith(".css"),
						L = _ ? '[rel="stylesheet"]' : "";
					if (document.querySelector(`link[href="${y}"]${L}`)) return;
					const g = document.createElement("link");
					if (
						((g.rel = _ ? "stylesheet" : Ct),
						_ || (g.as = "script"),
						(g.crossOrigin = ""),
						(g.href = y),
						f && g.setAttribute("nonce", f),
						document.head.appendChild(g),
						_)
					)
						return new Promise((j, m) => {
							g.addEventListener("load", j),
								g.addEventListener("error", () =>
									m(new Error(`Unable to preload CSS for ${y}`)),
								);
						});
				}),
			);
		}
		function p(h) {
			const f = new Event("vite:preloadError", { cancelable: !0 });
			if (((f.payload = h), window.dispatchEvent(f), !f.defaultPrevented)) throw h;
		}
		return s.then((h) => {
			for (const f of h || []) f.status === "rejected" && p(f.reason);
			return o().catch(p);
		});
	},
	Yt = [
		{ path: "/", redirect: "/home" },
		{
			path: "/home",
			name: "Home",
			component: () =>
				A(
					() => import("./Home-BlUsb_74.js"),
					__vite__mapDeps([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]),
				),
		},
		{
			path: "/attendance",
			name: "Attendance",
			component: () =>
				A(
					() => import("./Attendance-BQn40tyw.js"),
					__vite__mapDeps([11, 1, 2, 3, 12, 13, 7, 9, 5, 14, 15, 16, 10]),
				),
		},
		{
			path: "/leave",
			name: "Leave",
			component: () =>
				A(
					() => import("./Leave-ChQtt7Lk.js"),
					__vite__mapDeps([17, 1, 2, 3, 12, 4, 5, 6, 13, 7, 8, 14, 15, 16, 10]),
				),
		},
		{
			path: "/expenses",
			name: "Expenses",
			component: () =>
				A(
					() => import("./Expenses-CQTc1zQ3.js"),
					__vite__mapDeps([18, 1, 2, 3, 4, 5, 6, 13, 7, 19, 14, 15, 16, 10]),
				),
		},
		{
			path: "/requests/:type/:name",
			name: "Request",
			component: () =>
				A(
					() => import("./Request-DoyYVLTK.js"),
					__vite__mapDeps([20, 1, 2, 3, 12, 4, 5, 6, 13, 7, 9, 14, 15, 16, 10]),
				),
		},
		{ path: "/expenses/:name", redirect: (t) => `/requests/expense/${t.params.name}` },
		{
			path: "/payslips",
			name: "Payslips",
			component: () =>
				A(
					() => import("./Payslips-F3aI3vOI.js"),
					__vite__mapDeps([21, 1, 2, 3, 12, 4, 5, 6, 13, 7, 9, 16, 10]),
				),
		},
		{
			path: "/payslips/:name",
			name: "Payslip",
			component: () =>
				A(
					() => import("./Payslip-BFdUwNvP.js"),
					__vite__mapDeps([22, 1, 2, 3, 12, 4, 5, 6, 13, 7, 9, 19]),
				),
		},
		{
			path: "/advances",
			name: "Advances",
			component: () =>
				A(
					() => import("./Advances-C1gOEb44.js"),
					__vite__mapDeps([23, 1, 2, 3, 4, 5, 6, 13, 7, 14, 15, 16, 10]),
				),
		},
		{
			path: "/appraisals",
			name: "Appraisals",
			component: () =>
				A(
					() => import("./Appraisals-CSn8NeWg.js"),
					__vite__mapDeps([24, 1, 2, 3, 4, 5, 6, 13, 7, 25]),
				),
		},
		{
			path: "/appraisals/:name",
			name: "Appraisal",
			component: () =>
				A(
					() => import("./Appraisal-BhPEP4AC.js"),
					__vite__mapDeps([26, 1, 2, 3, 12, 4, 5, 6, 13, 7, 9, 19, 8, 25]),
				),
		},
		{
			path: "/directory",
			name: "Directory",
			component: () =>
				A(() => import("./Directory-Cjc6dUR2.js"), __vite__mapDeps([27, 3, 1, 2, 7, 5])),
		},
		{
			path: "/directory/:employee",
			name: "Colleague",
			component: () =>
				A(
					() => import("./Colleague-BqZPReOK.js"),
					__vite__mapDeps([28, 1, 2, 3, 29, 7, 8]),
				),
		},
		{
			path: "/org-chart",
			name: "OrgChart",
			component: () =>
				A(() => import("./OrgChart-ajZIQDO0.js"), __vite__mapDeps([30, 1, 2, 3, 5])),
		},
		{
			path: "/holidays",
			name: "Holidays",
			component: () =>
				A(
					() => import("./Holidays-BDD9rzGz.js"),
					__vite__mapDeps([31, 3, 1, 2, 12, 4, 5, 6, 13, 7, 9]),
				),
		},
		{
			path: "/documents",
			name: "Documents",
			component: () =>
				A(
					() => import("./Documents-BiXqaXm2.js"),
					__vite__mapDeps([32, 3, 1, 2, 12, 4, 5, 6, 7]),
				),
		},
		{
			path: "/me",
			name: "Profile",
			component: () =>
				A(
					() => import("./Profile-D_m9OkBn.js"),
					__vite__mapDeps([33, 1, 2, 3, 29, 7, 4, 5, 6, 9, 8, 10]),
				),
		},
		{
			path: "/x/:slug",
			name: "Extension",
			component: () =>
				A(
					() => import("./Extension-CSwDbGjD.js"),
					__vite__mapDeps([34, 1, 2, 3, 13, 7, 4, 5, 6, 9, 19, 15, 16, 10]),
				),
		},
		{ path: "/:pathMatch(.*)*", redirect: "/home" },
	],
	ge = Xe({ history: et("/hrms"), routes: Yt, scrollBehavior: () => ({ top: 0 }) }),
	re = tt(Rt);
nt("resourceFetcher", at);
re.use(rt);
re.use(ge);
re.component("Button", st);
re.component("FormControl", ot);
re.provide("$session", ne);
ge.beforeEach((t, o, i) =>
	me(void 0, null, function* () {
		if (!ne.isLoggedIn) {
			window.location.href = `/login?redirect-to=${encodeURIComponent(
				"/hrms" + t.fullPath,
			)}`;
			return;
		}
		if (!U.data && !U.loading)
			try {
				yield U.fetch();
			} catch (d) {}
		i();
	}),
);
ge.isReady().then(() =>
	me(void 0, null, function* () {
		re.mount("#app");
	}),
);
export {
	on as a,
	sn as b,
	Q as c,
	Mt as d,
	un as e,
	jt as f,
	Ft as g,
	Nt as h,
	Wt as i,
	qt as j,
	zt as k,
	Bt as l,
	rn as m,
	Jt as n,
	Kt as o,
	Ut as p,
	Zt as q,
	Gt as r,
	cn as s,
	an as t,
	Qt as u,
	Xt as v,
	nn as w,
	en as x,
	tn as y,
};
