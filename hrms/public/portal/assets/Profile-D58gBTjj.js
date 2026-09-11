var ie = Object.defineProperty,
	ue = Object.defineProperties;
var re = Object.getOwnPropertyDescriptors;
var Y = Object.getOwnPropertySymbols;
var de = Object.prototype.hasOwnProperty,
	ce = Object.prototype.propertyIsEnumerable;
var K = (g, f, m) =>
		f in g
			? ie(g, f, { enumerable: !0, configurable: !0, writable: !0, value: m })
			: (g[f] = m),
	Z = (g, f) => {
		for (var m in f || (f = {})) de.call(f, m) && K(g, m, f[m]);
		if (Y) for (var m of Y(f)) ce.call(f, m) && K(g, m, f[m]);
		return g;
	},
	Q = (g, f) => ue(g, re(f));
var X = (g, f, m) =>
	new Promise((E, _) => {
		var N = (k) => {
				try {
					u(m.next(k));
				} catch (w) {
					_(w);
				}
			},
			a = (k) => {
				try {
					u(m.throw(k));
				} catch (w) {
					_(w);
				}
			},
			u = (k) => (k.done ? E(k.value) : Promise.resolve(k.value).then(N, a));
		u((m = m.apply(g, f)).next());
	});
import {
	o as r,
	h as b,
	F as D,
	i as S,
	d as h,
	w as n,
	e as i,
	t as C,
	g as o,
	O as me,
	z as R,
	v as U,
	f as e,
	I as $,
	k as M,
	s as ve,
	J as pe,
	V as fe,
	B as F,
	a as x,
	L as _e,
	Z as ge,
	$ as ye,
	a0 as O,
	n as be,
	a1 as ke,
	u as xe,
	b as he,
	q as $e,
} from "./frappe-ui-rHlwnvVy.js";
import { a as Ce, _ as y, b as we } from "./SectionCard-0tgyDAFI.js";
import { _ as Ae } from "./IdentityBand-BrhYzFba.js";
import { _ as ee } from "./DataTable-BY05XQx8.js";
import { _ as c } from "./FieldRow-C13lI4HG.js";
import { _ as ae } from "./PersonRow-LB2-2vnj.js";
import { _ as q } from "./EmptyState-0_BFjfJU.js";
import { w as Ee, x as T, y as le, d as j, a as I, s as Be } from "./index-6wvshjQq.js";
import { n as De, a as Ne, e as Pe, b as Re } from "./toast-BxUFHbEO.js";
import "./StatusBadge-ZWn2FvVw.js";
const Me = { class: "flex flex-col gap-3" },
	Se = { class: "nums text-base-medium text-ink-gray-5" },
	Ve = {
		__name: "BalanceBars",
		props: { balances: { type: Array, default: () => [] } },
		setup(g) {
			return (f, m) => {
				var E;
				return (
					r(),
					b("div", Me, [
						(r(!0),
						b(
							D,
							null,
							S(
								g.balances,
								(_) => (
									r(),
									h(
										o(me),
										{
											key: _.leave_type,
											value: _.pct,
											size: "md",
											label: _.leave_type,
										},
										{
											hint: n(() => [
												i(
													"span",
													Se,
													C(_.balance) + " of " + C(_.allocated),
													1,
												),
											]),
											_: 2,
										},
										1032,
										["value", "label"],
									)
								),
							),
							128,
						)),
						(E = g.balances) != null && E.length
							? R("", !0)
							: (r(),
							  h(q, { key: 0, message: "No leave allocated for this period." })),
					])
				);
			};
		},
	},
	Oe = { class: "flex flex-col gap-3" },
	Te = { class: "grid gap-3 sm:grid-cols-2" },
	je = { key: 0, class: "flex flex-col gap-2" },
	qe = { class: "grid gap-3 sm:grid-cols-2" },
	Fe = { class: "text-base text-ink-gray-5" },
	We = {
		class: "flex items-center justify-between gap-2 rounded-4 border border-outline-gray-2 px-2 py-1.5 text-p-base text-ink-gray-6",
	},
	ze = { class: "truncate" },
	He = { class: "text-base text-ink-gray-5" },
	Le = { class: "flex items-center justify-between gap-3" },
	Ie = { class: "ml-auto flex gap-2" },
	Ue = {
		__name: "EditDialog",
		props: {
			open: Boolean,
			title: String,
			fields: { type: Array, default: () => [] },
			values: { type: Object, default: () => ({}) },
		},
		emits: ["update:open", "saved"],
		setup(g, { emit: f }) {
			const m = g,
				E = f,
				_ = F({}),
				N = F(!1),
				a = x({ get: () => m.open, set: (p) => E("update:open", p) }),
				u = x(() => m.fields.filter((p) => !p.locked)),
				k = x(() => m.fields.filter((p) => p.locked)),
				w = x(() => {
					const p = k.value.map((v) => v.label);
					return p.length === 1
						? `${p[0]} is`
						: `${p.slice(0, -1).join(", ")} and ${p.at(-1)} are`;
				}),
				z = x(() =>
					u.value.some((p) => {
						var v, d;
						return (
							((v = _.value[p.fieldname]) != null ? v : "") !==
							((d = m.values[p.fieldname]) != null ? d : "")
						);
					}),
				);
			U(
				() => m.open,
				(p) => {
					p &&
						(_.value = Object.fromEntries(
							u.value.map((v) => {
								var d;
								return [v.fieldname, (d = m.values[v.fieldname]) != null ? d : ""];
							}),
						));
				},
				{ immediate: !0 },
			);
			function W() {
				a.value = !1;
			}
			function H() {
				return X(this, null, function* () {
					var p, v;
					N.value = !0;
					try {
						const d = {};
						for (const B of u.value) {
							const V = (p = _.value[B.fieldname]) != null ? p : "";
							V !== ((v = m.values[B.fieldname]) != null ? v : "") &&
								(d[B.fieldname] = V);
						}
						yield Ee.submit({ values: JSON.stringify(d) }),
							De("Profile updated"),
							E("saved"),
							W();
					} catch (d) {
						Ne("Could not save", Pe(d, "Try again in a moment."));
					} finally {
						N.value = !1;
					}
				});
			}
			return (p, v) => (
				r(),
				h(
					o(fe),
					{
						open: a.value,
						"onUpdate:open": v[0] || (v[0] = (d) => (a.value = d)),
						title: g.title,
						size: "md",
					},
					{
						default: n(() => [
							i("div", Oe, [
								i("div", Te, [
									(r(!0),
									b(
										D,
										null,
										S(
											u.value,
											(d) => (
												r(),
												b(
													"div",
													{
														key: d.fieldname,
														class: ve(d.fullWidth && "sm:col-span-2"),
													},
													[
														e(
															o(pe),
															{
																modelValue: _.value[d.fieldname],
																"onUpdate:modelValue": (B) =>
																	(_.value[d.fieldname] = B),
																type: d.type || "text",
																label: d.label,
																options: d.options,
																placeholder: d.placeholder,
															},
															null,
															8,
															[
																"modelValue",
																"onUpdate:modelValue",
																"type",
																"label",
																"options",
																"placeholder",
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
								k.value.length
									? (r(),
									  b("div", je, [
											i("div", qe, [
												(r(!0),
												b(
													D,
													null,
													S(
														k.value,
														(d) => (
															r(),
															b(
																"div",
																{
																	key: d.fieldname,
																	class: "flex flex-col gap-1",
																},
																[
																	i("span", Fe, C(d.label), 1),
																	i("div", We, [
																		i(
																			"span",
																			ze,
																			C(
																				g.values[
																					d.fieldname
																				] || "Not set",
																			),
																			1,
																		),
																		v[1] ||
																			(v[1] = i(
																				"span",
																				{
																					class: "h-3 w-3 shrink-0 text-ink-gray-4 lucide-lock",
																					"aria-hidden":
																						"true",
																				},
																				null,
																				-1,
																			)),
																	]),
																],
															)
														),
													),
													128,
												)),
											]),
											i("p", He, C(w.value) + " managed by HR.", 1),
									  ]))
									: R("", !0),
							]),
						]),
						actions: n(() => [
							i("div", Le, [
								v[4] ||
									(v[4] = i(
										"span",
										{ class: "hidden text-base text-ink-gray-5 sm:block" },
										" Visible to your reporting manager ",
										-1,
									)),
								i("div", Ie, [
									e(
										o($),
										{ variant: "subtle", onClick: W },
										{
											default: n(() => [
												...(v[2] || (v[2] = [M("Cancel", -1)])),
											]),
											_: 1,
										},
									),
									e(
										o($),
										{
											variant: "solid",
											loading: N.value,
											disabled: !z.value,
											onClick: H,
										},
										{
											default: n(() => [
												...(v[3] || (v[3] = [M(" Save ", -1)])),
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
					["open", "title"],
				)
			);
		},
	},
	Ge = { class: "flex flex-col gap-3.5" },
	Je = { class: "flex flex-col" },
	Ye = { class: "flex flex-col" },
	Ke = { class: "flex flex-col gap-3.5" },
	Ze = { class: "flex flex-col" },
	Qe = { key: 0, class: "flex flex-col" },
	Xe = { class: "flex flex-col gap-3.5" },
	ea = { class: "flex flex-col" },
	aa = { class: "px-3.5 pb-3.5" },
	la = { class: "nums w-20 shrink-0 text-base text-ink-gray-5" },
	ta = { class: "text-p-base text-ink-gray-8" },
	na = { class: "flex flex-col gap-3.5" },
	sa = { key: 0, class: "flex flex-col gap-3" },
	oa = { class: "flex flex-wrap items-center gap-1.5" },
	ia = { class: "ml-1 text-base text-ink-gray-5" },
	ua = { class: "font-semibold text-ink-gray-9" },
	ra = { class: "flex flex-col gap-3.5" },
	da = { class: "flex flex-col" },
	ca = { class: "flex flex-col" },
	ma = { class: "flex flex-col gap-3.5" },
	va = { key: 0, class: "flex flex-col" },
	pa = { class: "flex flex-col" },
	Aa = {
		__name: "Profile",
		setup(g) {
			const f = [
					{ key: "about", label: "About" },
					{ key: "job", label: "Job" },
					{ key: "pay", label: "Pay" },
					{ key: "time", label: "Time" },
					{ key: "documents", label: "Documents" },
				],
				m = [
					{ key: "period", label: "Period", primary: !0 },
					{
						key: "gross_pay",
						label: "Gross",
						align: "right",
						nums: !0,
						muted: !0,
						hideOnMobile: !0,
					},
					{ key: "net_pay", label: "Net Pay", align: "right", nums: !0 },
				],
				E = [
					{ key: "file_name", label: "File", primary: !0 },
					{ key: "modified", label: "Added", nums: !0, muted: !0, align: "right" },
				],
				_ = xe(),
				N = he(),
				a = x(() => T.data),
				u = x(() => {
					var t;
					return ((t = a.value) == null ? void 0 : t.employee) || {};
				}),
				k = x(() => le.data || {}),
				w = F(f.some((t) => t.key === _.query.tab) ? _.query.tab : "about");
			U(
				() => _.query.tab,
				(t) => {
					t && f.some((s) => s.key === t) && (w.value = t);
				},
			),
				U(w, (t) => {
					t !== _.query.tab && N.replace({ query: Q(Z({}, _.query), { tab: t }) });
				});
			const z = x(() =>
					[u.value.designation, u.value.department, u.value.branch]
						.filter(Boolean)
						.join(" · "),
				),
				W = x(() => {
					var t;
					return [
						u.value.status && {
							tone: u.value.status === "Active" ? "available" : "inactive",
							label: u.value.status,
						},
						u.value.employment_type && {
							tone: "gray",
							label: u.value.employment_type,
						},
						((t = u.value.shift) == null ? void 0 : t.name) && {
							tone: "gray",
							label: u.value.shift.name,
						},
					].filter(Boolean);
				}),
				H = x(() => {
					var t, s, A;
					return [
						{ label: "Employee ID", value: u.value.employee_number },
						{
							label: "Joined",
							value: u.value.date_of_joining ? j(u.value.date_of_joining) : null,
						},
						{ label: "Tenure", value: u.value.tenure },
						{
							label: "Reports To",
							value:
								(A =
									(s = (t = a.value) == null ? void 0 : t.reporting) == null
										? void 0
										: s.manager) == null
									? void 0
									: A.employee_name,
						},
						u.value.grade ? { label: "Grade", value: u.value.grade } : null,
					].filter(Boolean);
				}),
				p = x(() => {
					var t, s, A, l;
					return !!(
						((s = (t = a.value) == null ? void 0 : t.emergency) != null &&
							s.person_to_be_contacted) ||
						((l = (A = a.value) == null ? void 0 : A.emergency) != null &&
							l.emergency_phone_number)
					);
				}),
				v = F(!1),
				d = F("personal"),
				B = x(() => ({
					personal: {
						title: "Edit Personal Details",
						fields: [
							{
								fieldname: "gender",
								label: "Gender",
								type: "select",
								options: L(k.value.gender),
							},
							{
								fieldname: "blood_group",
								label: "Blood group",
								type: "select",
								options: L(k.value.blood_group),
							},
							{
								fieldname: "marital_status",
								label: "Marital status",
								type: "select",
								options: L(k.value.marital_status),
							},
							{ fieldname: "employee_name", label: "Full name", locked: !0 },
							{ fieldname: "date_of_birth", label: "Date of birth", locked: !0 },
						],
						values: () => {
							var t;
							return ((t = a.value) == null ? void 0 : t.personal) || {};
						},
					},
					contact: {
						title: "Edit Contact Details",
						fields: [
							{
								fieldname: "personal_email",
								label: "Personal email",
								type: "email",
							},
							{ fieldname: "cell_number", label: "Mobile", type: "text" },
							{ fieldname: "company_email", label: "Work email", locked: !0 },
						],
						values: () => {
							var t;
							return ((t = a.value) == null ? void 0 : t.contact) || {};
						},
					},
					addresses: {
						title: "Edit Addresses",
						fields: [
							{
								fieldname: "current_address",
								label: "Current address",
								type: "textarea",
								fullWidth: !0,
							},
							{
								fieldname: "permanent_address",
								label: "Permanent address",
								type: "textarea",
								fullWidth: !0,
							},
						],
						values: () => {
							var t;
							return ((t = a.value) == null ? void 0 : t.addresses) || {};
						},
					},
					emergency: {
						title: p.value ? "Edit Emergency Contact" : "Add Emergency Contact",
						fields: [
							{ fieldname: "person_to_be_contacted", label: "Name", type: "text" },
							{ fieldname: "relation", label: "Relation", type: "text" },
							{
								fieldname: "emergency_phone_number",
								label: "Phone",
								type: "text",
								fullWidth: !0,
							},
						],
						values: () => {
							var t;
							return ((t = a.value) == null ? void 0 : t.emergency) || {};
						},
					},
					bank: {
						title: "Edit Bank Account",
						fields: [
							{ fieldname: "bank_name", label: "Bank", type: "text" },
							{ fieldname: "bank_ac_no", label: "Account number", type: "text" },
							{ fieldname: "ifsc_code", label: "IFSC", type: "text", fullWidth: !0 },
						],
						values: () => {
							var t, s, A, l, G, J;
							return {
								bank_name:
									(A =
										(s = (t = a.value) == null ? void 0 : t.pay) == null
											? void 0
											: s.bank) == null
										? void 0
										: A.bank_name,
								ifsc_code:
									(J =
										(G = (l = a.value) == null ? void 0 : l.pay) == null
											? void 0
											: G.bank) == null
										? void 0
										: J.ifsc,
							};
						},
					},
				})),
				V = x(() => B.value[d.value] || B.value.personal),
				te = x(() => V.value.values() || {});
			function L(t) {
				return ["", ...(t || [])];
			}
			function P(t) {
				(d.value = t), (v.value = !0);
			}
			function ne() {
				window.location.href = `mailto:${u.value.company_email}`;
			}
			function se() {
				Re(
					"Job details are managed by HR",
					"Ask your HR team to update these. A request workflow is not wired up yet.",
				);
			}
			function oe(t) {
				t.file_url && window.open(t.file_url, "_blank", "noopener");
			}
			return (
				_e(() => {
					T.fetch(), le.fetch();
				}),
				(t, s) => {
					const A = $e("RouterLink");
					return (
						r(),
						h(
							we,
							{ loading: o(T).loading && !o(T).data },
							{
								default: n(() => [
									a.value
										? (r(),
										  b(
												D,
												{ key: 0 },
												[
													e(Ce, {
														title: "Profile",
														subtitle: "Your personal and work details",
													}),
													e(
														Ae,
														{
															name: u.value.employee_name,
															image: u.value.image,
															meta: z.value,
															badges: W.value,
															facts: H.value,
														},
														{
															actions: n(() => [
																u.value.company_email
																	? (r(),
																	  h(
																			o($),
																			{
																				key: 0,
																				variant: "subtle",
																				onClick: ne,
																			},
																			{
																				default: n(() => [
																					...(s[11] ||
																						(s[11] = [
																							M(
																								"Email",
																								-1,
																							),
																						])),
																				]),
																				_: 1,
																			},
																	  ))
																	: R("", !0),
																e(
																	o($),
																	{
																		variant: "subtle",
																		onClick:
																			s[0] ||
																			(s[0] = (l) =>
																				t.$router.push(
																					"/org-chart",
																				)),
																	},
																	{
																		default: n(() => [
																			...(s[12] ||
																				(s[12] = [
																					M(
																						"Org Chart",
																						-1,
																					),
																				])),
																		]),
																		_: 1,
																	},
																),
																e(
																	o($),
																	{
																		variant: "solid",
																		onClick:
																			s[1] ||
																			(s[1] = (l) =>
																				P("personal")),
																	},
																	{
																		default: n(() => [
																			...(s[13] ||
																				(s[13] = [
																					M(
																						"Edit Profile",
																						-1,
																					),
																				])),
																		]),
																		_: 1,
																	},
																),
															]),
															_: 1,
														},
														8,
														[
															"name",
															"image",
															"meta",
															"badges",
															"facts",
														],
													),
													e(
														o(ke),
														{
															modelValue: w.value,
															"onUpdate:modelValue":
																s[8] ||
																(s[8] = (l) => (w.value = l)),
														},
														{
															default: n(() => [
																e(
																	o(ge),
																	{ variant: "underline" },
																	{
																		default: n(() => [
																			(r(),
																			b(
																				D,
																				null,
																				S(f, (l) =>
																					e(
																						o(ye),
																						{
																							key: l.key,
																							value: l.key,
																							label: l.label,
																						},
																						null,
																						8,
																						[
																							"value",
																							"label",
																						],
																					),
																				),
																				64,
																			)),
																		]),
																		_: 1,
																	},
																),
																e(
																	o(O),
																	{
																		value: "about",
																		class: "grid items-start gap-3.5 pt-3.5 lg:grid-cols-2",
																	},
																	{
																		default: n(() => [
																			i("div", Ge, [
																				e(
																					y,
																					{
																						title: "Personal",
																						action: "Edit",
																						onAction:
																							s[2] ||
																							(s[2] =
																								(
																									l,
																								) =>
																									P(
																										"personal",
																									)),
																					},
																					{
																						default: n(
																							() => [
																								i(
																									"dl",
																									Je,
																									[
																										e(
																											c,
																											{
																												label: "Full name",
																												value: a
																													.value
																													.personal
																													.employee_name,
																												locked: "",
																											},
																											null,
																											8,
																											[
																												"value",
																											],
																										),
																										e(
																											c,
																											{
																												label: "Date of birth",
																												value: a
																													.value
																													.personal
																													.date_of_birth
																													? o(
																															j,
																													  )(
																															a
																																.value
																																.personal
																																.date_of_birth,
																													  )
																													: "",
																												locked: "",
																											},
																											null,
																											8,
																											[
																												"value",
																											],
																										),
																										e(
																											c,
																											{
																												label: "Gender",
																												value: a
																													.value
																													.personal
																													.gender,
																											},
																											null,
																											8,
																											[
																												"value",
																											],
																										),
																										e(
																											c,
																											{
																												label: "Blood group",
																												value: a
																													.value
																													.personal
																													.blood_group,
																											},
																											null,
																											8,
																											[
																												"value",
																											],
																										),
																										e(
																											c,
																											{
																												label: "Marital status",
																												value: a
																													.value
																													.personal
																													.marital_status,
																											},
																											null,
																											8,
																											[
																												"value",
																											],
																										),
																									],
																								),
																							],
																						),
																						_: 1,
																					},
																				),
																				e(
																					y,
																					{
																						title: "Addresses",
																						action: "Edit",
																						onAction:
																							s[3] ||
																							(s[3] =
																								(
																									l,
																								) =>
																									P(
																										"addresses",
																									)),
																					},
																					{
																						default: n(
																							() => [
																								i(
																									"dl",
																									Ye,
																									[
																										e(
																											c,
																											{
																												label: "Current",
																												value: a
																													.value
																													.addresses
																													.current_address,
																											},
																											null,
																											8,
																											[
																												"value",
																											],
																										),
																										e(
																											c,
																											{
																												label: "Permanent",
																												value: a
																													.value
																													.addresses
																													.permanent_address,
																											},
																											null,
																											8,
																											[
																												"value",
																											],
																										),
																									],
																								),
																							],
																						),
																						_: 1,
																					},
																				),
																			]),
																			i("div", Ke, [
																				e(
																					y,
																					{
																						title: "Contact",
																						action: "Edit",
																						onAction:
																							s[4] ||
																							(s[4] =
																								(
																									l,
																								) =>
																									P(
																										"contact",
																									)),
																					},
																					{
																						default: n(
																							() => [
																								i(
																									"dl",
																									Ze,
																									[
																										e(
																											c,
																											{
																												label: "Work email",
																												value: a
																													.value
																													.contact
																													.company_email,
																												locked: "",
																											},
																											null,
																											8,
																											[
																												"value",
																											],
																										),
																										e(
																											c,
																											{
																												label: "Personal email",
																												value: a
																													.value
																													.contact
																													.personal_email,
																											},
																											null,
																											8,
																											[
																												"value",
																											],
																										),
																										e(
																											c,
																											{
																												label: "Mobile",
																												value: a
																													.value
																													.contact
																													.cell_number,
																												nums: "",
																											},
																											null,
																											8,
																											[
																												"value",
																											],
																										),
																									],
																								),
																							],
																						),
																						_: 1,
																					},
																				),
																				e(
																					y,
																					{
																						title: "Emergency Contact",
																						action: p.value
																							? "Edit"
																							: "Add",
																						onAction:
																							s[6] ||
																							(s[6] =
																								(
																									l,
																								) =>
																									P(
																										"emergency",
																									)),
																					},
																					{
																						default: n(
																							() => [
																								p.value
																									? (r(),
																									  b(
																											"dl",
																											Qe,
																											[
																												e(
																													c,
																													{
																														label: "Name",
																														value: a
																															.value
																															.emergency
																															.person_to_be_contacted,
																													},
																													null,
																													8,
																													[
																														"value",
																													],
																												),
																												e(
																													c,
																													{
																														label: "Relation",
																														value: a
																															.value
																															.emergency
																															.relation,
																													},
																													null,
																													8,
																													[
																														"value",
																													],
																												),
																												e(
																													c,
																													{
																														label: "Phone",
																														value: a
																															.value
																															.emergency
																															.emergency_phone_number,
																														nums: "",
																													},
																													null,
																													8,
																													[
																														"value",
																													],
																												),
																											],
																									  ))
																									: (r(),
																									  h(
																											q,
																											{
																												key: 1,
																												message:
																													"No emergency contact on file.",
																												action: "Add a Contact",
																												onAction:
																													s[5] ||
																													(s[5] =
																														(
																															l,
																														) =>
																															P(
																																"emergency",
																															)),
																											},
																									  )),
																							],
																						),
																						_: 1,
																					},
																					8,
																					["action"],
																				),
																			]),
																		]),
																		_: 1,
																	},
																),
																e(
																	o(O),
																	{
																		value: "job",
																		class: "grid items-start gap-3.5 pt-3.5 lg:grid-cols-2",
																	},
																	{
																		default: n(() => [
																			i("div", Xe, [
																				e(
																					y,
																					{
																						title: "Position",
																						"readonly-label":
																							"HR-owned",
																					},
																					{
																						default: n(
																							() => [
																								i(
																									"dl",
																									ea,
																									[
																										e(
																											c,
																											{
																												label: "Designation",
																												value: a
																													.value
																													.position
																													.designation,
																												locked: "",
																											},
																											null,
																											8,
																											[
																												"value",
																											],
																										),
																										e(
																											c,
																											{
																												label: "Department",
																												value: a
																													.value
																													.position
																													.department,
																												locked: "",
																											},
																											null,
																											8,
																											[
																												"value",
																											],
																										),
																										e(
																											c,
																											{
																												label: "Employment type",
																												value: a
																													.value
																													.position
																													.employment_type,
																												locked: "",
																											},
																											null,
																											8,
																											[
																												"value",
																											],
																										),
																										e(
																											c,
																											{
																												label: "Grade",
																												value: a
																													.value
																													.position
																													.grade,
																												locked: "",
																											},
																											null,
																											8,
																											[
																												"value",
																											],
																										),
																										e(
																											c,
																											{
																												label: "Location",
																												value: a
																													.value
																													.position
																													.branch,
																												locked: "",
																											},
																											null,
																											8,
																											[
																												"value",
																											],
																										),
																									],
																								),
																								e(
																									o(
																										$,
																									),
																									{
																										class: "-ml-2 self-start",
																										variant:
																											"ghost",
																										label: "Request a change",
																										onClick:
																											se,
																									},
																								),
																							],
																						),
																						_: 1,
																					},
																				),
																				e(
																					y,
																					{
																						title: "History",
																						padded: !1,
																					},
																					{
																						default: n(
																							() => [
																								i(
																									"ul",
																									aa,
																									[
																										(r(
																											!0,
																										),
																										b(
																											D,
																											null,
																											S(
																												a
																													.value
																													.history,
																												(
																													l,
																												) => (
																													r(),
																													b(
																														"li",
																														{
																															key:
																																l.date +
																																l.label,
																															class: "flex gap-3 border-b border-outline-gray-1 py-2 last:border-0",
																														},
																														[
																															i(
																																"span",
																																la,
																																C(
																																	l.date
																																		? o(
																																				j,
																																		  )(
																																				l.date,
																																				"MMM YYYY",
																																		  )
																																		: "—",
																																),
																																1,
																															),
																															i(
																																"span",
																																ta,
																																C(
																																	l.label,
																																),
																																1,
																															),
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
																						_: 1,
																					},
																				),
																			]),
																			i("div", na, [
																				e(
																					y,
																					{
																						title: "Reporting",
																					},
																					{
																						action: n(
																							() => [
																								e(
																									o(
																										$,
																									),
																									{
																										variant:
																											"ghost",
																										route: "/org-chart",
																										label: "Org chart",
																									},
																								),
																							],
																						),
																						default: n(
																							() => [
																								a
																									.value
																									.reporting
																									.manager ||
																								a
																									.value
																									.reporting
																									.skip
																									? (r(),
																									  b(
																											"div",
																											sa,
																											[
																												a
																													.value
																													.reporting
																													.manager
																													? (r(),
																													  h(
																															ae,
																															{
																																key: 0,
																																name: a
																																	.value
																																	.reporting
																																	.manager
																																	.employee_name,
																																image: a
																																	.value
																																	.reporting
																																	.manager
																																	.image,
																																meta: `${
																																	a
																																		.value
																																		.reporting
																																		.manager
																																		.designation ||
																																	""
																																} · Manager`,
																																to: `/directory/${a.value.reporting.manager.name}`,
																																size: "2xl",
																															},
																															null,
																															8,
																															[
																																"name",
																																"image",
																																"meta",
																																"to",
																															],
																													  ))
																													: R(
																															"",
																															!0,
																													  ),
																												a
																													.value
																													.reporting
																													.skip
																													? (r(),
																													  h(
																															ae,
																															{
																																key: 1,
																																name: a
																																	.value
																																	.reporting
																																	.skip
																																	.employee_name,
																																image: a
																																	.value
																																	.reporting
																																	.skip
																																	.image,
																																meta: `${
																																	a
																																		.value
																																		.reporting
																																		.skip
																																		.designation ||
																																	""
																																} · Skip-level`,
																																to: `/directory/${a.value.reporting.skip.name}`,
																																size: "2xl",
																															},
																															null,
																															8,
																															[
																																"name",
																																"image",
																																"meta",
																																"to",
																															],
																													  ))
																													: R(
																															"",
																															!0,
																													  ),
																											],
																									  ))
																									: (r(),
																									  h(
																											q,
																											{
																												key: 1,
																												message:
																													"No reporting manager set.",
																											},
																									  )),
																							],
																						),
																						_: 1,
																					},
																				),
																				a.value.reporting
																					.peers.length
																					? (r(),
																					  h(
																							y,
																							{
																								key: 0,
																								title: "Team",
																							},
																							{
																								action: n(
																									() => [
																										e(
																											o(
																												$,
																											),
																											{
																												variant:
																													"ghost",
																												route: "/directory",
																												label: "Directory",
																											},
																										),
																									],
																								),
																								default:
																									n(
																										() => [
																											i(
																												"div",
																												oa,
																												[
																													(r(
																														!0,
																													),
																													b(
																														D,
																														null,
																														S(
																															a
																																.value
																																.reporting
																																.peers,
																															(
																																l,
																															) => (
																																r(),
																																h(
																																	A,
																																	{
																																		key: l.name,
																																		to: `/directory/${l.name}`,
																																		title: l.employee_name,
																																	},
																																	{
																																		default:
																																			n(
																																				() => [
																																					e(
																																						o(
																																							be,
																																						),
																																						{
																																							label: l.employee_name,
																																							image: l.image,
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
																																		_: 2,
																																	},
																																	1032,
																																	[
																																		"to",
																																		"title",
																																	],
																																)
																															),
																														),
																														128,
																													)),
																													i(
																														"span",
																														ia,
																														C(
																															a
																																.value
																																.reporting
																																.peers
																																.length,
																														) +
																															" peers ",
																														1,
																													),
																												],
																											),
																										],
																									),
																								_: 1,
																							},
																					  ))
																					: R("", !0),
																			]),
																		]),
																		_: 1,
																	},
																),
																e(
																	o(O),
																	{
																		value: "pay",
																		class: "grid items-start gap-3.5 pt-3.5 lg:grid-cols-2",
																	},
																	{
																		default: n(() => [
																			e(
																				y,
																				{
																					title: "Recent Payslips",
																					padded: !1,
																				},
																				{
																					action: n(
																						() => [
																							e(
																								o(
																									$,
																								),
																								{
																									variant:
																										"ghost",
																									route: "/payslips",
																									label: "View all",
																								},
																							),
																						],
																					),
																					default: n(
																						() => [
																							e(
																								ee,
																								{
																									columns:
																										m,
																									rows: a
																										.value
																										.pay
																										.slips,
																									"empty-message":
																										"No payslips issued yet.",
																								},
																								{
																									"cell-gross_pay":
																										n(
																											({
																												row: l,
																											}) => [
																												M(
																													C(
																														o(
																															I,
																														)(
																															l.gross_pay,
																														),
																													),
																													1,
																												),
																											],
																										),
																									"cell-net_pay":
																										n(
																											({
																												row: l,
																											}) => [
																												i(
																													"span",
																													ua,
																													C(
																														o(
																															I,
																														)(
																															l.net_pay,
																														),
																													),
																													1,
																												),
																											],
																										),
																									_: 1,
																								},
																								8,
																								[
																									"rows",
																								],
																							),
																						],
																					),
																					_: 1,
																				},
																			),
																			i("div", ra, [
																				e(
																					y,
																					{
																						title: "Bank Account",
																						action: "Edit",
																						onAction:
																							s[7] ||
																							(s[7] =
																								(
																									l,
																								) =>
																									P(
																										"bank",
																									)),
																					},
																					{
																						default: n(
																							() => [
																								i(
																									"dl",
																									da,
																									[
																										e(
																											c,
																											{
																												label: "Bank",
																												value: a
																													.value
																													.pay
																													.bank
																													.bank_name,
																											},
																											null,
																											8,
																											[
																												"value",
																											],
																										),
																										e(
																											c,
																											{
																												label: "Account",
																												value: a
																													.value
																													.pay
																													.bank
																													.account,
																												nums: "",
																											},
																											null,
																											8,
																											[
																												"value",
																											],
																										),
																										e(
																											c,
																											{
																												label: "IFSC",
																												value: a
																													.value
																													.pay
																													.bank
																													.ifsc,
																											},
																											null,
																											8,
																											[
																												"value",
																											],
																										),
																									],
																								),
																							],
																						),
																						_: 1,
																					},
																				),
																				e(
																					y,
																					{
																						title: "Tax",
																					},
																					{
																						action: n(
																							() => [
																								e(
																									o(
																										$,
																									),
																									{
																										variant:
																											"ghost",
																										route: "/payslips",
																										label: "Declare",
																									},
																								),
																							],
																						),
																						default: n(
																							() => [
																								i(
																									"dl",
																									ca,
																									[
																										e(
																											c,
																											{
																												label: "Declared",
																												value: o(
																													I,
																												)(
																													a
																														.value
																														.pay
																														.tax
																														.declared,
																												),
																												nums: "",
																											},
																											null,
																											8,
																											[
																												"value",
																											],
																										),
																										e(
																											c,
																											{
																												label: "Status",
																												value: a
																													.value
																													.pay
																													.tax
																													.has_declaration
																													? "Submitted"
																													: "Not declared",
																											},
																											null,
																											8,
																											[
																												"value",
																											],
																										),
																									],
																								),
																							],
																						),
																						_: 1,
																					},
																				),
																			]),
																		]),
																		_: 1,
																	},
																),
																e(
																	o(O),
																	{
																		value: "time",
																		class: "grid items-start gap-3.5 pt-3.5 lg:grid-cols-2",
																	},
																	{
																		default: n(() => [
																			i("div", ma, [
																				e(
																					y,
																					{
																						title: "Leave Balance",
																					},
																					{
																						action: n(
																							() => [
																								e(
																									o(
																										$,
																									),
																									{
																										variant:
																											"ghost",
																										route: "/leave",
																										label: "Open leave",
																									},
																								),
																							],
																						),
																						default: n(
																							() => [
																								e(
																									Ve,
																									{
																										balances:
																											a
																												.value
																												.time
																												.balances,
																									},
																									null,
																									8,
																									[
																										"balances",
																									],
																								),
																							],
																						),
																						_: 1,
																					},
																				),
																				e(
																					y,
																					{
																						title: "Upcoming Leave",
																					},
																					{
																						default: n(
																							() => [
																								a
																									.value
																									.time
																									.upcoming_leave
																									.length
																									? (r(),
																									  b(
																											"dl",
																											va,
																											[
																												(r(
																													!0,
																												),
																												b(
																													D,
																													null,
																													S(
																														a
																															.value
																															.time
																															.upcoming_leave,
																														(
																															l,
																														) => (
																															r(),
																															h(
																																c,
																																{
																																	key:
																																		l.from_date +
																																		l.leave_type,
																																	label: o(
																																		j,
																																	)(
																																		l.from_date,
																																		"D MMM",
																																	),
																																	value: `${
																																		l.leave_type
																																	}, ${
																																		l.total_leave_days
																																	} day${
																																		l.total_leave_days ===
																																		1
																																			? ""
																																			: "s"
																																	} (${
																																		l.status
																																	})`,
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
																											],
																									  ))
																									: (r(),
																									  h(
																											q,
																											{
																												key: 1,
																												message:
																													"No leave booked ahead.",
																											},
																									  )),
																							],
																						),
																						_: 1,
																					},
																				),
																			]),
																			e(
																				y,
																				{
																					title: "Shift and Calendar",
																					"readonly-label":
																						"HR-owned",
																				},
																				{
																					default: n(
																						() => {
																							var l;
																							return [
																								i(
																									"dl",
																									pa,
																									[
																										e(
																											c,
																											{
																												label: "Assigned shift",
																												value:
																													(l =
																														a
																															.value
																															.time
																															.shift) ==
																													null
																														? void 0
																														: l.name,
																												locked: "",
																											},
																											null,
																											8,
																											[
																												"value",
																											],
																										),
																										e(
																											c,
																											{
																												label: "Timing",
																												value: o(
																													Be,
																												)(
																													a
																														.value
																														.time
																														.shift,
																												),
																												locked: "",
																												nums: "",
																											},
																											null,
																											8,
																											[
																												"value",
																											],
																										),
																										e(
																											c,
																											{
																												label: "Weekly off",
																												value: a
																													.value
																													.time
																													.weekly_off,
																												locked: "",
																											},
																											null,
																											8,
																											[
																												"value",
																											],
																										),
																										e(
																											c,
																											{
																												label: "Holiday list",
																												value: a
																													.value
																													.time
																													.holiday_list,
																												locked: "",
																											},
																											null,
																											8,
																											[
																												"value",
																											],
																										),
																									],
																								),
																							];
																						},
																					),
																					_: 1,
																				},
																			),
																		]),
																		_: 1,
																	},
																),
																e(
																	o(O),
																	{
																		value: "documents",
																		class: "grid items-start gap-3.5 pt-3.5 lg:grid-cols-2",
																	},
																	{
																		default: n(() => [
																			e(
																				y,
																				{
																					title: "My Documents",
																					padded: !1,
																				},
																				{
																					default: n(
																						() => [
																							e(
																								ee,
																								{
																									columns:
																										E,
																									rows: a
																										.value
																										.documents,
																									clickable:
																										"",
																									"empty-message":
																										"Nothing attached to your employee record yet.",
																									onRowClick:
																										oe,
																								},
																								{
																									"cell-modified":
																										n(
																											({
																												row: l,
																											}) => [
																												M(
																													C(
																														o(
																															j,
																														)(
																															l.modified,
																														),
																													),
																													1,
																												),
																											],
																										),
																									_: 1,
																								},
																								8,
																								[
																									"rows",
																								],
																							),
																						],
																					),
																					_: 1,
																				},
																			),
																			e(
																				y,
																				{
																					title: "From the Company",
																				},
																				{
																					action: n(
																						() => [
																							e(
																								o(
																									$,
																								),
																								{
																									variant:
																										"ghost",
																									route: "/documents",
																									label: "Open",
																								},
																							),
																						],
																					),
																					default: n(
																						() => [
																							e(q, {
																								message:
																									"Company-wide policies and handbooks live under Documents.",
																							}),
																						],
																					),
																					_: 1,
																				},
																			),
																		]),
																		_: 1,
																	},
																),
															]),
															_: 1,
														},
														8,
														["modelValue"],
													),
													e(
														Ue,
														{
															open: v.value,
															"onUpdate:open":
																s[9] ||
																(s[9] = (l) => (v.value = l)),
															title: V.value.title,
															fields: V.value.fields,
															values: te.value,
															onSaved:
																s[10] ||
																(s[10] = (l) => o(T).reload()),
														},
														null,
														8,
														["open", "title", "fields", "values"],
													),
												],
												64,
										  ))
										: R("", !0),
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
export { Aa as default };
