var ie = Object.defineProperty,
	ue = Object.defineProperties;
var re = Object.getOwnPropertyDescriptors;
var J = Object.getOwnPropertySymbols;
var de = Object.prototype.hasOwnProperty,
	me = Object.prototype.propertyIsEnumerable;
var K = (g, f, m) =>
		f in g
			? ie(g, f, { enumerable: !0, configurable: !0, writable: !0, value: m })
			: (g[f] = m),
	Z = (g, f) => {
		for (var m in f || (f = {})) de.call(f, m) && K(g, m, f[m]);
		if (J) for (var m of J(f)) me.call(f, m) && K(g, m, f[m]);
		return g;
	},
	Q = (g, f) => ue(g, re(f));
var X = (g, f, m) =>
	new Promise((R, k) => {
		var B = (y) => {
				try {
					u(m.next(y));
				} catch (C) {
					k(C);
				}
			},
			l = (y) => {
				try {
					u(m.throw(y));
				} catch (C) {
					k(C);
				}
			},
			u = (y) => (y.done ? R(y.value) : Promise.resolve(y.value).then(B, l));
		u((m = m.apply(g, f)).next());
	});
import {
	v as I,
	o as v,
	d as $,
	w as n,
	e as i,
	f as e,
	g as s,
	I as h,
	k as P,
	h as x,
	F as N,
	i as V,
	s as ce,
	J as ve,
	t as A,
	z as S,
	U as pe,
	B as q,
	a as b,
	L as fe,
	Y as ge,
	Z as _e,
	$ as O,
	n as ye,
	a0 as be,
	u as ke,
	b as xe,
	q as he,
} from "./frappe-ui-D0k6koYp.js";
import { a as $e, _, b as Ce } from "./SectionCard-C5Qs8pBJ.js";
import { _ as we } from "./IdentityBand-BZ37_HBf.js";
import { _ as ee } from "./DataTable-BPI_hH2T.js";
import { _ as d } from "./FieldRow-DoxIhPye.js";
import { _ as le } from "./PersonRow-2k8WhDWN.js";
import { _ as Ae } from "./BalanceBars-9ROF_iIl.js";
import { _ as W } from "./EmptyState-38_uLDf3.js";
import { u as Ee, v as T, w as ae, d as j, a as z, s as Be } from "./index-BSaIzYPn.js";
import { n as De, a as Pe, e as Ne, b as Re } from "./toast-BPVivXt-.js";
import "./StatusBadge-sSVuNJEI.js";
const Me = { class: "flex flex-col gap-3" },
	Se = { class: "grid gap-3 sm:grid-cols-2" },
	Ve = { key: 0, class: "flex flex-col gap-2" },
	Oe = { class: "grid gap-3 sm:grid-cols-2" },
	Te = { class: "text-base text-ink-gray-5" },
	je = {
		class: "flex items-center justify-between gap-2 rounded-4 border border-outline-gray-2 px-2 py-1.5 text-p-base text-ink-gray-6",
	},
	qe = { class: "truncate" },
	Fe = { class: "text-base text-ink-gray-5" },
	We = { class: "flex items-center justify-between gap-3" },
	He = { class: "ml-auto flex gap-2" },
	Le = {
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
				R = f,
				k = q({}),
				B = q(!1),
				l = b({ get: () => m.open, set: (p) => R("update:open", p) }),
				u = b(() => m.fields.filter((p) => !p.locked)),
				y = b(() => m.fields.filter((p) => p.locked)),
				C = b(() => {
					const p = y.value.map((c) => c.label);
					return p.length === 1
						? `${p[0]} is`
						: `${p.slice(0, -1).join(", ")} and ${p.at(-1)} are`;
				}),
				H = b(() =>
					u.value.some((p) => {
						var c, r;
						return (
							((c = k.value[p.fieldname]) != null ? c : "") !==
							((r = m.values[p.fieldname]) != null ? r : "")
						);
					}),
				);
			I(
				() => m.open,
				(p) => {
					p &&
						(k.value = Object.fromEntries(
							u.value.map((c) => {
								var r;
								return [c.fieldname, (r = m.values[c.fieldname]) != null ? r : ""];
							}),
						));
				},
				{ immediate: !0 },
			);
			function F() {
				l.value = !1;
			}
			function L() {
				return X(this, null, function* () {
					var p, c;
					B.value = !0;
					try {
						const r = {};
						for (const E of u.value) {
							const M = (p = k.value[E.fieldname]) != null ? p : "";
							M !== ((c = m.values[E.fieldname]) != null ? c : "") &&
								(r[E.fieldname] = M);
						}
						yield Ee.submit({ values: JSON.stringify(r) }),
							De("Profile updated"),
							R("saved"),
							F();
					} catch (r) {
						Pe("Could not save", Ne(r, "Try again in a moment."));
					} finally {
						B.value = !1;
					}
				});
			}
			return (p, c) => (
				v(),
				$(
					s(pe),
					{
						open: l.value,
						"onUpdate:open": c[0] || (c[0] = (r) => (l.value = r)),
						title: g.title,
						size: "md",
					},
					{
						"body-content": n(() => [
							i("div", Me, [
								i("div", Se, [
									(v(!0),
									x(
										N,
										null,
										V(
											u.value,
											(r) => (
												v(),
												x(
													"div",
													{
														key: r.fieldname,
														class: ce(r.fullWidth && "sm:col-span-2"),
													},
													[
														e(
															s(ve),
															{
																modelValue: k.value[r.fieldname],
																"onUpdate:modelValue": (E) =>
																	(k.value[r.fieldname] = E),
																type: r.type || "text",
																label: r.label,
																options: r.options,
																placeholder: r.placeholder,
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
								y.value.length
									? (v(),
									  x("div", Ve, [
											i("div", Oe, [
												(v(!0),
												x(
													N,
													null,
													V(
														y.value,
														(r) => (
															v(),
															x(
																"div",
																{
																	key: r.fieldname,
																	class: "flex flex-col gap-1",
																},
																[
																	i("span", Te, A(r.label), 1),
																	i("div", je, [
																		i(
																			"span",
																			qe,
																			A(
																				g.values[
																					r.fieldname
																				] || "Not set",
																			),
																			1,
																		),
																		c[1] ||
																			(c[1] = i(
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
											i("p", Fe, A(C.value) + " managed by HR.", 1),
									  ]))
									: S("", !0),
							]),
						]),
						actions: n(() => [
							i("div", We, [
								c[4] ||
									(c[4] = i(
										"span",
										{ class: "hidden text-base text-ink-gray-5 sm:block" },
										" Visible to your reporting manager ",
										-1,
									)),
								i("div", He, [
									e(
										s(h),
										{ variant: "subtle", onClick: F },
										{
											default: n(() => [
												...(c[2] || (c[2] = [P("Cancel", -1)])),
											]),
											_: 1,
										},
									),
									e(
										s(h),
										{
											variant: "solid",
											loading: B.value,
											disabled: !H.value,
											onClick: L,
										},
										{
											default: n(() => [
												...(c[3] || (c[3] = [P(" Save ", -1)])),
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
	Ue = { class: "flex flex-col gap-3.5" },
	ze = { class: "flex flex-col" },
	Ie = { class: "flex flex-col" },
	Ye = { class: "flex flex-col gap-3.5" },
	Ge = { class: "flex flex-col" },
	Je = { key: 0, class: "flex flex-col" },
	Ke = { class: "flex flex-col gap-3.5" },
	Ze = { class: "flex flex-col" },
	Qe = { class: "px-3.5 pb-3.5" },
	Xe = { class: "nums w-20 shrink-0 text-base text-ink-gray-5" },
	el = { class: "text-p-base text-ink-gray-8" },
	ll = { class: "flex flex-col gap-3.5" },
	al = { key: 0, class: "flex flex-col gap-3" },
	tl = { class: "flex flex-wrap items-center gap-1.5" },
	nl = { class: "ml-1 text-base text-ink-gray-5" },
	ol = { class: "font-semibold text-ink-gray-9" },
	sl = { class: "flex flex-col gap-3.5" },
	il = { class: "flex flex-col" },
	ul = { class: "flex flex-col" },
	rl = { class: "flex flex-col gap-3.5" },
	dl = { key: 0, class: "flex flex-col" },
	ml = { class: "flex flex-col" },
	Cl = {
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
				R = [
					{ key: "file_name", label: "File", primary: !0 },
					{ key: "modified", label: "Added", nums: !0, muted: !0, align: "right" },
				],
				k = ke(),
				B = xe(),
				l = b(() => T.data),
				u = b(() => {
					var t;
					return ((t = l.value) == null ? void 0 : t.employee) || {};
				}),
				y = b(() => ae.data || {}),
				C = q(f.some((t) => t.key === k.query.tab) ? k.query.tab : "about");
			I(
				() => k.query.tab,
				(t) => {
					t && f.some((o) => o.key === t) && (C.value = t);
				},
			),
				I(C, (t) => {
					t !== k.query.tab && B.replace({ query: Q(Z({}, k.query), { tab: t }) });
				});
			const H = b(() =>
					[u.value.designation, u.value.department, u.value.branch]
						.filter(Boolean)
						.join(" · "),
				),
				F = b(() => {
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
				L = b(() => {
					var t, o, w;
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
								(w =
									(o = (t = l.value) == null ? void 0 : t.reporting) == null
										? void 0
										: o.manager) == null
									? void 0
									: w.employee_name,
						},
						u.value.grade ? { label: "Grade", value: u.value.grade } : null,
					].filter(Boolean);
				}),
				p = b(() => {
					var t, o, w, a;
					return !!(
						((o = (t = l.value) == null ? void 0 : t.emergency) != null &&
							o.person_to_be_contacted) ||
						((a = (w = l.value) == null ? void 0 : w.emergency) != null &&
							a.emergency_phone_number)
					);
				}),
				c = q(!1),
				r = q("personal"),
				E = b(() => ({
					personal: {
						title: "Edit Personal Details",
						fields: [
							{
								fieldname: "gender",
								label: "Gender",
								type: "select",
								options: U(y.value.gender),
							},
							{
								fieldname: "blood_group",
								label: "Blood group",
								type: "select",
								options: U(y.value.blood_group),
							},
							{
								fieldname: "marital_status",
								label: "Marital status",
								type: "select",
								options: U(y.value.marital_status),
							},
							{ fieldname: "employee_name", label: "Full name", locked: !0 },
							{ fieldname: "date_of_birth", label: "Date of birth", locked: !0 },
						],
						values: () => {
							var t;
							return ((t = l.value) == null ? void 0 : t.personal) || {};
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
							return ((t = l.value) == null ? void 0 : t.contact) || {};
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
							return ((t = l.value) == null ? void 0 : t.addresses) || {};
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
							return ((t = l.value) == null ? void 0 : t.emergency) || {};
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
							var t, o, w, a, Y, G;
							return {
								bank_name:
									(w =
										(o = (t = l.value) == null ? void 0 : t.pay) == null
											? void 0
											: o.bank) == null
										? void 0
										: w.bank_name,
								ifsc_code:
									(G =
										(Y = (a = l.value) == null ? void 0 : a.pay) == null
											? void 0
											: Y.bank) == null
										? void 0
										: G.ifsc,
							};
						},
					},
				})),
				M = b(() => E.value[r.value] || E.value.personal),
				te = b(() => M.value.values() || {});
			function U(t) {
				return ["", ...(t || [])];
			}
			function D(t) {
				(r.value = t), (c.value = !0);
			}
			function ne() {
				window.location.href = `mailto:${u.value.company_email}`;
			}
			function oe() {
				Re(
					"Job details are managed by HR",
					"Ask your HR team to update these. A request workflow is not wired up yet.",
				);
			}
			function se(t) {
				t.file_url && window.open(t.file_url, "_blank", "noopener");
			}
			return (
				fe(() => {
					T.fetch(), ae.fetch();
				}),
				(t, o) => {
					const w = he("RouterLink");
					return (
						v(),
						$(
							Ce,
							{ loading: s(T).loading && !s(T).data },
							{
								default: n(() => [
									l.value
										? (v(),
										  x(
												N,
												{ key: 0 },
												[
													e($e, {
														title: "Profile",
														subtitle: "Your personal and work details",
													}),
													e(
														we,
														{
															name: u.value.employee_name,
															image: u.value.image,
															meta: H.value,
															badges: F.value,
															facts: L.value,
														},
														{
															actions: n(() => [
																u.value.company_email
																	? (v(),
																	  $(
																			s(h),
																			{
																				key: 0,
																				variant: "subtle",
																				onClick: ne,
																			},
																			{
																				default: n(() => [
																					...(o[11] ||
																						(o[11] = [
																							P(
																								"Email",
																								-1,
																							),
																						])),
																				]),
																				_: 1,
																			},
																	  ))
																	: S("", !0),
																e(
																	s(h),
																	{
																		variant: "subtle",
																		onClick:
																			o[0] ||
																			(o[0] = (a) =>
																				t.$router.push(
																					"/org-chart",
																				)),
																	},
																	{
																		default: n(() => [
																			...(o[12] ||
																				(o[12] = [
																					P(
																						"Org Chart",
																						-1,
																					),
																				])),
																		]),
																		_: 1,
																	},
																),
																e(
																	s(h),
																	{
																		variant: "solid",
																		onClick:
																			o[1] ||
																			(o[1] = (a) =>
																				D("personal")),
																	},
																	{
																		default: n(() => [
																			...(o[13] ||
																				(o[13] = [
																					P(
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
														s(be),
														{
															modelValue: C.value,
															"onUpdate:modelValue":
																o[8] ||
																(o[8] = (a) => (C.value = a)),
														},
														{
															default: n(() => [
																e(
																	s(ge),
																	{ variant: "underline" },
																	{
																		default: n(() => [
																			(v(),
																			x(
																				N,
																				null,
																				V(f, (a) =>
																					e(
																						s(_e),
																						{
																							key: a.key,
																							value: a.key,
																							label: a.label,
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
																	s(O),
																	{
																		value: "about",
																		class: "grid items-start gap-3.5 pt-3.5 lg:grid-cols-2",
																	},
																	{
																		default: n(() => [
																			i("div", Ue, [
																				e(
																					_,
																					{
																						title: "Personal",
																						action: "Edit",
																						onAction:
																							o[2] ||
																							(o[2] =
																								(
																									a,
																								) =>
																									D(
																										"personal",
																									)),
																					},
																					{
																						default: n(
																							() => [
																								i(
																									"dl",
																									ze,
																									[
																										e(
																											d,
																											{
																												label: "Full name",
																												value: l
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
																											d,
																											{
																												label: "Date of birth",
																												value: l
																													.value
																													.personal
																													.date_of_birth
																													? s(
																															j,
																													  )(
																															l
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
																											d,
																											{
																												label: "Gender",
																												value: l
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
																											d,
																											{
																												label: "Blood group",
																												value: l
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
																											d,
																											{
																												label: "Marital status",
																												value: l
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
																					_,
																					{
																						title: "Addresses",
																						action: "Edit",
																						onAction:
																							o[3] ||
																							(o[3] =
																								(
																									a,
																								) =>
																									D(
																										"addresses",
																									)),
																					},
																					{
																						default: n(
																							() => [
																								i(
																									"dl",
																									Ie,
																									[
																										e(
																											d,
																											{
																												label: "Current",
																												value: l
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
																											d,
																											{
																												label: "Permanent",
																												value: l
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
																			i("div", Ye, [
																				e(
																					_,
																					{
																						title: "Contact",
																						action: "Edit",
																						onAction:
																							o[4] ||
																							(o[4] =
																								(
																									a,
																								) =>
																									D(
																										"contact",
																									)),
																					},
																					{
																						default: n(
																							() => [
																								i(
																									"dl",
																									Ge,
																									[
																										e(
																											d,
																											{
																												label: "Work email",
																												value: l
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
																											d,
																											{
																												label: "Personal email",
																												value: l
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
																											d,
																											{
																												label: "Mobile",
																												value: l
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
																					_,
																					{
																						title: "Emergency Contact",
																						action: p.value
																							? "Edit"
																							: "Add",
																						onAction:
																							o[6] ||
																							(o[6] =
																								(
																									a,
																								) =>
																									D(
																										"emergency",
																									)),
																					},
																					{
																						default: n(
																							() => [
																								p.value
																									? (v(),
																									  x(
																											"dl",
																											Je,
																											[
																												e(
																													d,
																													{
																														label: "Name",
																														value: l
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
																													d,
																													{
																														label: "Relation",
																														value: l
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
																													d,
																													{
																														label: "Phone",
																														value: l
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
																									: (v(),
																									  $(
																											W,
																											{
																												key: 1,
																												message:
																													"No emergency contact on file.",
																												action: "Add a Contact",
																												onAction:
																													o[5] ||
																													(o[5] =
																														(
																															a,
																														) =>
																															D(
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
																	s(O),
																	{
																		value: "job",
																		class: "grid items-start gap-3.5 pt-3.5 lg:grid-cols-2",
																	},
																	{
																		default: n(() => [
																			i("div", Ke, [
																				e(
																					_,
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
																									Ze,
																									[
																										e(
																											d,
																											{
																												label: "Designation",
																												value: l
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
																											d,
																											{
																												label: "Department",
																												value: l
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
																											d,
																											{
																												label: "Employment type",
																												value: l
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
																											d,
																											{
																												label: "Grade",
																												value: l
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
																											d,
																											{
																												label: "Location",
																												value: l
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
																									s(
																										h,
																									),
																									{
																										class: "-ml-2 self-start",
																										variant:
																											"ghost",
																										label: "Request a change",
																										onClick:
																											oe,
																									},
																								),
																							],
																						),
																						_: 1,
																					},
																				),
																				e(
																					_,
																					{
																						title: "History",
																						padded: !1,
																					},
																					{
																						default: n(
																							() => [
																								i(
																									"ul",
																									Qe,
																									[
																										(v(
																											!0,
																										),
																										x(
																											N,
																											null,
																											V(
																												l
																													.value
																													.history,
																												(
																													a,
																												) => (
																													v(),
																													x(
																														"li",
																														{
																															key:
																																a.date +
																																a.label,
																															class: "flex gap-3 border-b border-outline-gray-1 py-2 last:border-0",
																														},
																														[
																															i(
																																"span",
																																Xe,
																																A(
																																	a.date
																																		? s(
																																				j,
																																		  )(
																																				a.date,
																																				"MMM YYYY",
																																		  )
																																		: "—",
																																),
																																1,
																															),
																															i(
																																"span",
																																el,
																																A(
																																	a.label,
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
																			i("div", ll, [
																				e(
																					_,
																					{
																						title: "Reporting",
																					},
																					{
																						action: n(
																							() => [
																								e(
																									s(
																										h,
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
																								l
																									.value
																									.reporting
																									.manager ||
																								l
																									.value
																									.reporting
																									.skip
																									? (v(),
																									  x(
																											"div",
																											al,
																											[
																												l
																													.value
																													.reporting
																													.manager
																													? (v(),
																													  $(
																															le,
																															{
																																key: 0,
																																name: l
																																	.value
																																	.reporting
																																	.manager
																																	.employee_name,
																																image: l
																																	.value
																																	.reporting
																																	.manager
																																	.image,
																																meta: `${
																																	l
																																		.value
																																		.reporting
																																		.manager
																																		.designation ||
																																	""
																																} · Manager`,
																																to: `/directory/${l.value.reporting.manager.name}`,
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
																													: S(
																															"",
																															!0,
																													  ),
																												l
																													.value
																													.reporting
																													.skip
																													? (v(),
																													  $(
																															le,
																															{
																																key: 1,
																																name: l
																																	.value
																																	.reporting
																																	.skip
																																	.employee_name,
																																image: l
																																	.value
																																	.reporting
																																	.skip
																																	.image,
																																meta: `${
																																	l
																																		.value
																																		.reporting
																																		.skip
																																		.designation ||
																																	""
																																} · Skip-level`,
																																to: `/directory/${l.value.reporting.skip.name}`,
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
																													: S(
																															"",
																															!0,
																													  ),
																											],
																									  ))
																									: (v(),
																									  $(
																											W,
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
																				l.value.reporting
																					.peers.length
																					? (v(),
																					  $(
																							_,
																							{
																								key: 0,
																								title: "Team",
																							},
																							{
																								action: n(
																									() => [
																										e(
																											s(
																												h,
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
																												tl,
																												[
																													(v(
																														!0,
																													),
																													x(
																														N,
																														null,
																														V(
																															l
																																.value
																																.reporting
																																.peers,
																															(
																																a,
																															) => (
																																v(),
																																$(
																																	w,
																																	{
																																		key: a.name,
																																		to: `/directory/${a.name}`,
																																		title: a.employee_name,
																																	},
																																	{
																																		default:
																																			n(
																																				() => [
																																					e(
																																						s(
																																							ye,
																																						),
																																						{
																																							label: a.employee_name,
																																							image: a.image,
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
																														nl,
																														A(
																															l
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
																					: S("", !0),
																			]),
																		]),
																		_: 1,
																	},
																),
																e(
																	s(O),
																	{
																		value: "pay",
																		class: "grid items-start gap-3.5 pt-3.5 lg:grid-cols-2",
																	},
																	{
																		default: n(() => [
																			e(
																				_,
																				{
																					title: "Recent Payslips",
																					padded: !1,
																				},
																				{
																					action: n(
																						() => [
																							e(
																								s(
																									h,
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
																									rows: l
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
																												row: a,
																											}) => [
																												P(
																													A(
																														s(
																															z,
																														)(
																															a.gross_pay,
																														),
																													),
																													1,
																												),
																											],
																										),
																									"cell-net_pay":
																										n(
																											({
																												row: a,
																											}) => [
																												i(
																													"span",
																													ol,
																													A(
																														s(
																															z,
																														)(
																															a.net_pay,
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
																			i("div", sl, [
																				e(
																					_,
																					{
																						title: "Bank Account",
																						action: "Edit",
																						onAction:
																							o[7] ||
																							(o[7] =
																								(
																									a,
																								) =>
																									D(
																										"bank",
																									)),
																					},
																					{
																						default: n(
																							() => [
																								i(
																									"dl",
																									il,
																									[
																										e(
																											d,
																											{
																												label: "Bank",
																												value: l
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
																											d,
																											{
																												label: "Account",
																												value: l
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
																											d,
																											{
																												label: "IFSC",
																												value: l
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
																					_,
																					{
																						title: "Tax",
																					},
																					{
																						action: n(
																							() => [
																								e(
																									s(
																										h,
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
																									ul,
																									[
																										e(
																											d,
																											{
																												label: "Declared",
																												value: s(
																													z,
																												)(
																													l
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
																											d,
																											{
																												label: "Status",
																												value: l
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
																	s(O),
																	{
																		value: "time",
																		class: "grid items-start gap-3.5 pt-3.5 lg:grid-cols-2",
																	},
																	{
																		default: n(() => [
																			i("div", rl, [
																				e(
																					_,
																					{
																						title: "Leave Balance",
																					},
																					{
																						action: n(
																							() => [
																								e(
																									s(
																										h,
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
																									Ae,
																									{
																										balances:
																											l
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
																					_,
																					{
																						title: "Upcoming Leave",
																					},
																					{
																						default: n(
																							() => [
																								l
																									.value
																									.time
																									.upcoming_leave
																									.length
																									? (v(),
																									  x(
																											"dl",
																											dl,
																											[
																												(v(
																													!0,
																												),
																												x(
																													N,
																													null,
																													V(
																														l
																															.value
																															.time
																															.upcoming_leave,
																														(
																															a,
																														) => (
																															v(),
																															$(
																																d,
																																{
																																	key:
																																		a.from_date +
																																		a.leave_type,
																																	label: s(
																																		j,
																																	)(
																																		a.from_date,
																																		"D MMM",
																																	),
																																	value: `${
																																		a.leave_type
																																	}, ${
																																		a.total_leave_days
																																	} day${
																																		a.total_leave_days ===
																																		1
																																			? ""
																																			: "s"
																																	} (${
																																		a.status
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
																									: (v(),
																									  $(
																											W,
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
																				_,
																				{
																					title: "Shift and Calendar",
																					"readonly-label":
																						"HR-owned",
																				},
																				{
																					default: n(
																						() => {
																							var a;
																							return [
																								i(
																									"dl",
																									ml,
																									[
																										e(
																											d,
																											{
																												label: "Assigned shift",
																												value:
																													(a =
																														l
																															.value
																															.time
																															.shift) ==
																													null
																														? void 0
																														: a.name,
																												locked: "",
																											},
																											null,
																											8,
																											[
																												"value",
																											],
																										),
																										e(
																											d,
																											{
																												label: "Timing",
																												value: s(
																													Be,
																												)(
																													l
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
																											d,
																											{
																												label: "Weekly off",
																												value: l
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
																											d,
																											{
																												label: "Holiday list",
																												value: l
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
																	s(O),
																	{
																		value: "documents",
																		class: "grid items-start gap-3.5 pt-3.5 lg:grid-cols-2",
																	},
																	{
																		default: n(() => [
																			e(
																				_,
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
																										R,
																									rows: l
																										.value
																										.documents,
																									clickable:
																										"",
																									"empty-message":
																										"Nothing attached to your employee record yet.",
																									onRowClick:
																										se,
																								},
																								{
																									"cell-modified":
																										n(
																											({
																												row: a,
																											}) => [
																												P(
																													A(
																														s(
																															j,
																														)(
																															a.modified,
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
																				_,
																				{
																					title: "From the Company",
																				},
																				{
																					action: n(
																						() => [
																							e(
																								s(
																									h,
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
																							e(W, {
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
														Le,
														{
															open: c.value,
															"onUpdate:open":
																o[9] ||
																(o[9] = (a) => (c.value = a)),
															title: M.value.title,
															fields: M.value.fields,
															values: te.value,
															onSaved:
																o[10] ||
																(o[10] = (a) => s(T).reload()),
														},
														null,
														8,
														["open", "title", "fields", "values"],
													),
												],
												64,
										  ))
										: S("", !0),
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
export { Cl as default };
