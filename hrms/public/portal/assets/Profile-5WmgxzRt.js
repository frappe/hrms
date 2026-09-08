var ie = Object.defineProperty,
	ue = Object.defineProperties;
var re = Object.getOwnPropertyDescriptors;
var Y = Object.getOwnPropertySymbols;
var de = Object.prototype.hasOwnProperty,
	me = Object.prototype.propertyIsEnumerable;
var J = (y, p, c) =>
		p in y
			? ie(y, p, { enumerable: !0, configurable: !0, writable: !0, value: c })
			: (y[p] = c),
	K = (y, p) => {
		for (var c in p || (p = {})) de.call(p, c) && J(y, c, p[c]);
		if (Y) for (var c of Y(p)) me.call(p, c) && J(y, c, p[c]);
		return y;
	},
	Q = (y, p) => ue(y, re(p));
var X = (y, p, c) =>
	new Promise((M, h) => {
		var D = (x) => {
				try {
					s(c.next(x));
				} catch (A) {
					h(A);
				}
			},
			e = (x) => {
				try {
					s(c.throw(x));
				} catch (A) {
					h(A);
				}
			},
			s = (x) => (x.done ? M(x.value) : Promise.resolve(x.value).then(D, e));
		s((c = c.apply(y, p)).next());
	});
import {
	w as le,
	o as u,
	f as w,
	g as o,
	k as r,
	h as a,
	i as m,
	M as C,
	B as P,
	s as g,
	F as R,
	t as T,
	v as ce,
	N as ve,
	x as E,
	p as pe,
	C as V,
	Y as fe,
	a as k,
	e as F,
	u as ge,
	b as _e,
	P as ye,
	q as be,
	a4 as ke,
	j as xe,
} from "./frappe-ui-BQ9PgXrr.js";
import { _ as b, a as he } from "./SectionCard-u_7VCKnT.js";
import { _ as $e } from "./IdentityBand-BGB1Buc7.js";
import { _ as Z } from "./DataTable-vZ6Z-J3d.js";
import { _ as d } from "./FieldRow-DbBPtAxY.js";
import { _ as ee } from "./PersonRow-DZ4YBxpS.js";
import { _ as Ce } from "./BalanceBars-CBgUe-mJ.js";
import { _ as H } from "./EmptyState-DNwecFw5.js";
import { u as we, v as O, w as ae, d as j, b as z, s as Ae } from "./index-DKSqIuAQ.js";
import { n as Ee, a as Be, e as De, b as Ne } from "./toast-9qekBDJT.js";
import "./StatusBadge-Bqz4zlkD.js";
const Pe = { class: "flex flex-col gap-3" },
	Me = { class: "grid gap-3 sm:grid-cols-2" },
	Ve = { key: 0, class: "flex flex-col gap-2" },
	Re = { class: "grid gap-3 sm:grid-cols-2" },
	Se = { class: "text-base text-ink-gray-5" },
	Oe = {
		class: "flex items-center justify-between gap-2 rounded border border-outline-gray-2 px-2 py-1.5 text-p-base text-ink-gray-6",
	},
	je = { class: "truncate" },
	Te = { class: "text-base text-ink-gray-5" },
	Fe = { class: "flex items-center justify-between gap-3" },
	qe = { class: "ml-auto flex gap-2" },
	We = {
		__name: "EditDialog",
		props: {
			open: Boolean,
			title: String,
			fields: { type: Array, default: () => [] },
			values: { type: Object, default: () => ({}) },
		},
		emits: ["update:open", "saved"],
		setup(y, { emit: p }) {
			const c = y,
				M = p,
				h = F({}),
				D = F(!1),
				e = k({ get: () => c.open, set: (f) => M("update:open", f) }),
				s = k(() => c.fields.filter((f) => !f.locked)),
				x = k(() => c.fields.filter((f) => f.locked)),
				A = k(() => {
					const f = x.value.map((v) => v.label);
					return f.length === 1
						? `${f[0]} is`
						: `${f.slice(0, -1).join(", ")} and ${f.at(-1)} are`;
				}),
				q = k(() =>
					s.value.some((f) => {
						var v, i;
						return (
							((v = h.value[f.fieldname]) != null ? v : "") !==
							((i = c.values[f.fieldname]) != null ? i : "")
						);
					}),
				);
			le(
				() => c.open,
				(f) => {
					f &&
						(h.value = Object.fromEntries(
							s.value.map((v) => {
								var i;
								return [v.fieldname, (i = c.values[v.fieldname]) != null ? i : ""];
							}),
						));
				},
				{ immediate: !0 },
			);
			function W() {
				e.value = !1;
			}
			function I() {
				return X(this, null, function* () {
					var f, v;
					D.value = !0;
					try {
						const i = {};
						for (const B of s.value) {
							const S = (f = h.value[B.fieldname]) != null ? f : "";
							S !== ((v = c.values[B.fieldname]) != null ? v : "") &&
								(i[B.fieldname] = S);
						}
						yield we.submit({ values: JSON.stringify(i) }),
							Ee("Profile updated"),
							M("saved"),
							W();
					} catch (i) {
						Be("Could not save", De(i, "Try again in a moment."));
					} finally {
						D.value = !1;
					}
				});
			}
			return (f, v) => (
				u(),
				w(
					m(fe),
					{
						modelValue: e.value,
						"onUpdate:modelValue": v[0] || (v[0] = (i) => (e.value = i)),
						options: { title: y.title, size: "md" },
					},
					{
						"body-content": o(() => [
							r("div", Pe, [
								r("div", Me, [
									(u(!0),
									g(
										R,
										null,
										T(
											s.value,
											(i) => (
												u(),
												g(
													"div",
													{
														key: i.fieldname,
														class: ce(i.fullWidth && "sm:col-span-2"),
													},
													[
														a(
															m(ve),
															{
																modelValue: h.value[i.fieldname],
																"onUpdate:modelValue": (B) =>
																	(h.value[i.fieldname] = B),
																type: i.type || "text",
																label: i.label,
																options: i.options,
																placeholder: i.placeholder,
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
								x.value.length
									? (u(),
									  g("div", Ve, [
											r("div", Re, [
												(u(!0),
												g(
													R,
													null,
													T(
														x.value,
														(i) => (
															u(),
															g(
																"div",
																{
																	key: i.fieldname,
																	class: "flex flex-col gap-1",
																},
																[
																	r("span", Se, E(i.label), 1),
																	r("div", Oe, [
																		r(
																			"span",
																			je,
																			E(
																				y.values[
																					i.fieldname
																				] || "Not set",
																			),
																			1,
																		),
																		a(m(pe), {
																			name: "lock",
																			class: "h-3 w-3 shrink-0 text-ink-gray-4",
																		}),
																	]),
																],
															)
														),
													),
													128,
												)),
											]),
											r("p", Te, E(A.value) + " managed by HR.", 1),
									  ]))
									: V("", !0),
							]),
						]),
						actions: o(() => [
							r("div", Fe, [
								v[3] ||
									(v[3] = r(
										"span",
										{ class: "hidden text-base text-ink-gray-5 sm:block" },
										" Visible to your reporting manager ",
										-1,
									)),
								r("div", qe, [
									a(
										m(C),
										{ variant: "subtle", onClick: W },
										{
											default: o(() => [
												...(v[1] || (v[1] = [P("Cancel", -1)])),
											]),
											_: 1,
										},
									),
									a(
										m(C),
										{
											variant: "solid",
											loading: D.value,
											disabled: !q.value,
											onClick: I,
										},
										{
											default: o(() => [
												...(v[2] || (v[2] = [P(" Save ", -1)])),
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
	},
	He = { key: 0, class: "grid items-start gap-3.5 pt-3.5 lg:grid-cols-2" },
	Ie = { class: "flex flex-col gap-3.5" },
	Le = { class: "flex flex-col" },
	Ue = { class: "flex flex-col" },
	ze = { class: "flex flex-col gap-3.5" },
	Ge = { class: "flex flex-col" },
	Ye = { key: 0, class: "flex flex-col" },
	Je = { key: 1, class: "grid items-start gap-3.5 pt-3.5 lg:grid-cols-2" },
	Ke = { class: "flex flex-col gap-3.5" },
	Qe = { class: "flex flex-col" },
	Xe = { class: "px-3.5 pb-3.5" },
	Ze = { class: "nums w-20 shrink-0 text-base text-ink-gray-5" },
	ea = { class: "text-p-base text-ink-gray-8" },
	aa = { class: "flex flex-col gap-3.5" },
	la = { key: 0, class: "flex flex-col gap-3" },
	ta = { class: "flex flex-wrap items-center gap-1.5" },
	na = { class: "ml-1 text-base text-ink-gray-5" },
	oa = { key: 2, class: "grid items-start gap-3.5 pt-3.5 lg:grid-cols-2" },
	sa = { class: "font-semibold text-ink-gray-9" },
	ia = { class: "flex flex-col gap-3.5" },
	ua = { class: "flex flex-col" },
	ra = { class: "flex flex-col" },
	da = { key: 3, class: "grid items-start gap-3.5 pt-3.5 lg:grid-cols-2" },
	ma = { class: "flex flex-col gap-3.5" },
	ca = { key: 0, class: "flex flex-col" },
	va = { class: "flex flex-col" },
	pa = { key: 4, class: "grid items-start gap-3.5 pt-3.5 lg:grid-cols-2" },
	Ea = {
		__name: "Profile",
		setup(y) {
			const p = [
					{ key: "about", label: "About" },
					{ key: "job", label: "Job" },
					{ key: "pay", label: "Pay" },
					{ key: "time", label: "Time" },
					{ key: "documents", label: "Documents" },
				],
				c = [
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
				M = [
					{ key: "file_name", label: "File", primary: !0 },
					{ key: "modified", label: "Added", nums: !0, muted: !0, align: "right" },
				],
				h = ge(),
				D = _e(),
				e = k(() => O.data),
				s = k(() => {
					var l;
					return ((l = e.value) == null ? void 0 : l.employee) || {};
				}),
				x = k(() => ae.data || {}),
				A = F(p.some((l) => l.key === h.query.tab) ? h.query.tab : "about");
			le(
				() => h.query.tab,
				(l) => {
					l && p.some((t) => t.key === l) && (A.value = l);
				},
			);
			const q = k({
					get: () =>
						Math.max(
							0,
							p.findIndex((l) => l.key === A.value),
						),
					set: (l) => {
						var $;
						const t = ($ = p[l]) == null ? void 0 : $.key;
						!t ||
							t === A.value ||
							((A.value = t), D.replace({ query: Q(K({}, h.query), { tab: t }) }));
					},
				}),
				W = k(() =>
					[s.value.designation, s.value.department, s.value.branch]
						.filter(Boolean)
						.join(" · "),
				),
				I = k(() => {
					var l;
					return [
						s.value.status && {
							tone: s.value.status === "Active" ? "available" : "inactive",
							label: s.value.status,
						},
						s.value.employment_type && {
							tone: "gray",
							label: s.value.employment_type,
						},
						((l = s.value.shift) == null ? void 0 : l.name) && {
							tone: "gray",
							label: s.value.shift.name,
						},
					].filter(Boolean);
				}),
				f = k(() => {
					var l, t, $;
					return [
						{ label: "Employee ID", value: s.value.employee_number },
						{
							label: "Joined",
							value: s.value.date_of_joining ? j(s.value.date_of_joining) : null,
						},
						{ label: "Tenure", value: s.value.tenure },
						{
							label: "Reports To",
							value:
								($ =
									(t = (l = e.value) == null ? void 0 : l.reporting) == null
										? void 0
										: t.manager) == null
									? void 0
									: $.employee_name,
						},
						s.value.grade ? { label: "Grade", value: s.value.grade } : null,
					].filter(Boolean);
				}),
				v = k(() => {
					var l, t, $, _;
					return !!(
						((t = (l = e.value) == null ? void 0 : l.emergency) != null &&
							t.person_to_be_contacted) ||
						((_ = ($ = e.value) == null ? void 0 : $.emergency) != null &&
							_.emergency_phone_number)
					);
				}),
				i = F(!1),
				B = F("personal"),
				S = k(() => ({
					personal: {
						title: "Edit Personal Details",
						fields: [
							{
								fieldname: "gender",
								label: "Gender",
								type: "select",
								options: U(x.value.gender),
							},
							{
								fieldname: "blood_group",
								label: "Blood group",
								type: "select",
								options: U(x.value.blood_group),
							},
							{
								fieldname: "marital_status",
								label: "Marital status",
								type: "select",
								options: U(x.value.marital_status),
							},
							{ fieldname: "employee_name", label: "Full name", locked: !0 },
							{ fieldname: "date_of_birth", label: "Date of birth", locked: !0 },
						],
						values: () => {
							var l;
							return ((l = e.value) == null ? void 0 : l.personal) || {};
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
							var l;
							return ((l = e.value) == null ? void 0 : l.contact) || {};
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
							var l;
							return ((l = e.value) == null ? void 0 : l.addresses) || {};
						},
					},
					emergency: {
						title: v.value ? "Edit Emergency Contact" : "Add Emergency Contact",
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
							var l;
							return ((l = e.value) == null ? void 0 : l.emergency) || {};
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
							var l, t, $, _, n, G;
							return {
								bank_name:
									($ =
										(t = (l = e.value) == null ? void 0 : l.pay) == null
											? void 0
											: t.bank) == null
										? void 0
										: $.bank_name,
								ifsc_code:
									(G =
										(n = (_ = e.value) == null ? void 0 : _.pay) == null
											? void 0
											: n.bank) == null
										? void 0
										: G.ifsc,
							};
						},
					},
				})),
				L = k(() => S.value[B.value] || S.value.personal),
				te = k(() => L.value.values() || {});
			function U(l) {
				return ["", ...(l || [])];
			}
			function N(l) {
				(B.value = l), (i.value = !0);
			}
			function ne() {
				window.location.href = `mailto:${s.value.company_email}`;
			}
			function oe() {
				Ne(
					"Job details are managed by HR",
					"Ask your HR team to update these. A request workflow is not wired up yet.",
				);
			}
			function se(l) {
				l.file_url && window.open(l.file_url, "_blank", "noopener");
			}
			return (
				ye(() => {
					O.fetch(), ae.fetch();
				}),
				(l, t) => {
					const $ = be("RouterLink");
					return (
						u(),
						w(
							he,
							{ loading: m(O).loading && !m(O).data },
							{
								default: o(() => [
									e.value
										? (u(),
										  g(
												R,
												{ key: 0 },
												[
													a(
														$e,
														{
															name: s.value.employee_name,
															image: s.value.image,
															meta: W.value,
															badges: I.value,
															facts: f.value,
														},
														{
															actions: o(() => [
																s.value.company_email
																	? (u(),
																	  w(
																			m(C),
																			{
																				key: 0,
																				variant: "subtle",
																				onClick: ne,
																			},
																			{
																				default: o(() => [
																					...(t[11] ||
																						(t[11] = [
																							P(
																								"Email",
																								-1,
																							),
																						])),
																				]),
																				_: 1,
																			},
																	  ))
																	: V("", !0),
																a(
																	m(C),
																	{
																		variant: "subtle",
																		onClick:
																			t[0] ||
																			(t[0] = (_) =>
																				l.$router.push(
																					"/org-chart",
																				)),
																	},
																	{
																		default: o(() => [
																			...(t[12] ||
																				(t[12] = [
																					P(
																						"Org Chart",
																						-1,
																					),
																				])),
																		]),
																		_: 1,
																	},
																),
																a(
																	m(C),
																	{
																		variant: "solid",
																		onClick:
																			t[1] ||
																			(t[1] = (_) =>
																				N("personal")),
																	},
																	{
																		default: o(() => [
																			...(t[13] ||
																				(t[13] = [
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
													a(
														m(ke),
														{
															modelValue: q.value,
															"onUpdate:modelValue":
																t[8] ||
																(t[8] = (_) => (q.value = _)),
															tabs: p,
														},
														{
															"tab-panel": o(({ tab: _ }) => [
																_.key === "about"
																	? (u(),
																	  g("div", He, [
																			r("div", Ie, [
																				a(
																					b,
																					{
																						title: "Personal",
																						action: "Edit",
																						onAction:
																							t[2] ||
																							(t[2] =
																								(
																									n,
																								) =>
																									N(
																										"personal",
																									)),
																					},
																					{
																						default: o(
																							() => [
																								r(
																									"dl",
																									Le,
																									[
																										a(
																											d,
																											{
																												label: "Full name",
																												value: e
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
																										a(
																											d,
																											{
																												label: "Date of birth",
																												value: e
																													.value
																													.personal
																													.date_of_birth
																													? m(
																															j,
																													  )(
																															e
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
																										a(
																											d,
																											{
																												label: "Gender",
																												value: e
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
																										a(
																											d,
																											{
																												label: "Blood group",
																												value: e
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
																										a(
																											d,
																											{
																												label: "Marital status",
																												value: e
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
																				a(
																					b,
																					{
																						title: "Addresses",
																						action: "Edit",
																						onAction:
																							t[3] ||
																							(t[3] =
																								(
																									n,
																								) =>
																									N(
																										"addresses",
																									)),
																					},
																					{
																						default: o(
																							() => [
																								r(
																									"dl",
																									Ue,
																									[
																										a(
																											d,
																											{
																												label: "Current",
																												value: e
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
																										a(
																											d,
																											{
																												label: "Permanent",
																												value: e
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
																			r("div", ze, [
																				a(
																					b,
																					{
																						title: "Contact",
																						action: "Edit",
																						onAction:
																							t[4] ||
																							(t[4] =
																								(
																									n,
																								) =>
																									N(
																										"contact",
																									)),
																					},
																					{
																						default: o(
																							() => [
																								r(
																									"dl",
																									Ge,
																									[
																										a(
																											d,
																											{
																												label: "Work email",
																												value: e
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
																										a(
																											d,
																											{
																												label: "Personal email",
																												value: e
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
																										a(
																											d,
																											{
																												label: "Mobile",
																												value: e
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
																				a(
																					b,
																					{
																						title: "Emergency Contact",
																						action: v.value
																							? "Edit"
																							: "Add",
																						onAction:
																							t[6] ||
																							(t[6] =
																								(
																									n,
																								) =>
																									N(
																										"emergency",
																									)),
																					},
																					{
																						default: o(
																							() => [
																								v.value
																									? (u(),
																									  g(
																											"dl",
																											Ye,
																											[
																												a(
																													d,
																													{
																														label: "Name",
																														value: e
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
																												a(
																													d,
																													{
																														label: "Relation",
																														value: e
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
																												a(
																													d,
																													{
																														label: "Phone",
																														value: e
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
																									: (u(),
																									  w(
																											H,
																											{
																												key: 1,
																												message:
																													"No emergency contact on file.",
																												action: "Add a Contact",
																												onAction:
																													t[5] ||
																													(t[5] =
																														(
																															n,
																														) =>
																															N(
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
																	  ]))
																	: _.key === "job"
																	  ? (u(),
																	    g("div", Je, [
																				r("div", Ke, [
																					a(
																						b,
																						{
																							title: "Position",
																							"readonly-label":
																								"HR-owned",
																						},
																						{
																							default:
																								o(
																									() => [
																										r(
																											"dl",
																											Qe,
																											[
																												a(
																													d,
																													{
																														label: "Designation",
																														value: e
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
																												a(
																													d,
																													{
																														label: "Department",
																														value: e
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
																												a(
																													d,
																													{
																														label: "Employment type",
																														value: e
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
																												a(
																													d,
																													{
																														label: "Grade",
																														value: e
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
																												a(
																													d,
																													{
																														label: "Location",
																														value: e
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
																										a(
																											m(
																												C,
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
																					a(
																						b,
																						{
																							title: "History",
																							padded: !1,
																						},
																						{
																							default:
																								o(
																									() => [
																										r(
																											"ul",
																											Xe,
																											[
																												(u(
																													!0,
																												),
																												g(
																													R,
																													null,
																													T(
																														e
																															.value
																															.history,
																														(
																															n,
																														) => (
																															u(),
																															g(
																																"li",
																																{
																																	key:
																																		n.date +
																																		n.label,
																																	class: "flex gap-3 border-b border-outline-gray-1 py-2 last:border-0",
																																},
																																[
																																	r(
																																		"span",
																																		Ze,
																																		E(
																																			n.date
																																				? m(
																																						j,
																																				  )(
																																						n.date,
																																						"MMM YYYY",
																																				  )
																																				: "—",
																																		),
																																		1,
																																	),
																																	r(
																																		"span",
																																		ea,
																																		E(
																																			n.label,
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
																				r("div", aa, [
																					a(
																						b,
																						{
																							title: "Reporting",
																						},
																						{
																							action: o(
																								() => [
																									a(
																										m(
																											C,
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
																							default:
																								o(
																									() => [
																										e
																											.value
																											.reporting
																											.manager ||
																										e
																											.value
																											.reporting
																											.skip
																											? (u(),
																											  g(
																													"div",
																													la,
																													[
																														e
																															.value
																															.reporting
																															.manager
																															? (u(),
																															  w(
																																	ee,
																																	{
																																		key: 0,
																																		name: e
																																			.value
																																			.reporting
																																			.manager
																																			.employee_name,
																																		image: e
																																			.value
																																			.reporting
																																			.manager
																																			.image,
																																		meta: `${
																																			e
																																				.value
																																				.reporting
																																				.manager
																																				.designation ||
																																			""
																																		} · Manager`,
																																		to: `/directory/${e.value.reporting.manager.name}`,
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
																															: V(
																																	"",
																																	!0,
																															  ),
																														e
																															.value
																															.reporting
																															.skip
																															? (u(),
																															  w(
																																	ee,
																																	{
																																		key: 1,
																																		name: e
																																			.value
																																			.reporting
																																			.skip
																																			.employee_name,
																																		image: e
																																			.value
																																			.reporting
																																			.skip
																																			.image,
																																		meta: `${
																																			e
																																				.value
																																				.reporting
																																				.skip
																																				.designation ||
																																			""
																																		} · Skip-level`,
																																		to: `/directory/${e.value.reporting.skip.name}`,
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
																															: V(
																																	"",
																																	!0,
																															  ),
																													],
																											  ))
																											: (u(),
																											  w(
																													H,
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
																					e.value
																						.reporting
																						.peers
																						.length
																						? (u(),
																						  w(
																								b,
																								{
																									key: 0,
																									title: "Team",
																								},
																								{
																									action: o(
																										() => [
																											a(
																												m(
																													C,
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
																										o(
																											() => [
																												r(
																													"div",
																													ta,
																													[
																														(u(
																															!0,
																														),
																														g(
																															R,
																															null,
																															T(
																																e
																																	.value
																																	.reporting
																																	.peers,
																																(
																																	n,
																																) => (
																																	u(),
																																	w(
																																		$,
																																		{
																																			key: n.name,
																																			to: `/directory/${n.name}`,
																																			title: n.employee_name,
																																		},
																																		{
																																			default:
																																				o(
																																					() => [
																																						a(
																																							m(
																																								xe,
																																							),
																																							{
																																								label: n.employee_name,
																																								image: n.image,
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
																														r(
																															"span",
																															na,
																															E(
																																e
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
																						: V(
																								"",
																								!0,
																						  ),
																				]),
																	    ]))
																	  : _.key === "pay"
																	    ? (u(),
																	      g("div", oa, [
																					a(
																						b,
																						{
																							title: "Recent Payslips",
																							padded: !1,
																						},
																						{
																							action: o(
																								() => [
																									a(
																										m(
																											C,
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
																							default:
																								o(
																									() => [
																										a(
																											Z,
																											{
																												columns:
																													c,
																												rows: e
																													.value
																													.pay
																													.slips,
																												"empty-message":
																													"No payslips issued yet.",
																											},
																											{
																												"cell-gross_pay":
																													o(
																														({
																															row: n,
																														}) => [
																															P(
																																E(
																																	m(
																																		z,
																																	)(
																																		n.gross_pay,
																																	),
																																),
																																1,
																															),
																														],
																													),
																												"cell-net_pay":
																													o(
																														({
																															row: n,
																														}) => [
																															r(
																																"span",
																																sa,
																																E(
																																	m(
																																		z,
																																	)(
																																		n.net_pay,
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
																					r("div", ia, [
																						a(
																							b,
																							{
																								title: "Bank Account",
																								action: "Edit",
																								onAction:
																									t[7] ||
																									(t[7] =
																										(
																											n,
																										) =>
																											N(
																												"bank",
																											)),
																							},
																							{
																								default:
																									o(
																										() => [
																											r(
																												"dl",
																												ua,
																												[
																													a(
																														d,
																														{
																															label: "Bank",
																															value: e
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
																													a(
																														d,
																														{
																															label: "Account",
																															value: e
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
																													a(
																														d,
																														{
																															label: "IFSC",
																															value: e
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
																						a(
																							b,
																							{
																								title: "Tax",
																							},
																							{
																								action: o(
																									() => [
																										a(
																											m(
																												C,
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
																								default:
																									o(
																										() => [
																											r(
																												"dl",
																												ra,
																												[
																													a(
																														d,
																														{
																															label: "Declared",
																															value: m(
																																z,
																															)(
																																e
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
																													a(
																														d,
																														{
																															label: "Status",
																															value: e
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
																	      ]))
																	    : _.key === "time"
																	      ? (u(),
																	        g("div", da, [
																						r(
																							"div",
																							ma,
																							[
																								a(
																									b,
																									{
																										title: "Leave Balance",
																									},
																									{
																										action: o(
																											() => [
																												a(
																													m(
																														C,
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
																										default:
																											o(
																												() => [
																													a(
																														Ce,
																														{
																															balances:
																																e
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
																								a(
																									b,
																									{
																										title: "Upcoming Leave",
																									},
																									{
																										default:
																											o(
																												() => [
																													e
																														.value
																														.time
																														.upcoming_leave
																														.length
																														? (u(),
																														  g(
																																"dl",
																																ca,
																																[
																																	(u(
																																		!0,
																																	),
																																	g(
																																		R,
																																		null,
																																		T(
																																			e
																																				.value
																																				.time
																																				.upcoming_leave,
																																			(
																																				n,
																																			) => (
																																				u(),
																																				w(
																																					d,
																																					{
																																						key:
																																							n.from_date +
																																							n.leave_type,
																																						label: m(
																																							j,
																																						)(
																																							n.from_date,
																																							"D MMM",
																																						),
																																						value: `${
																																							n.leave_type
																																						}, ${
																																							n.total_leave_days
																																						} day${
																																							n.total_leave_days ===
																																							1
																																								? ""
																																								: "s"
																																						} (${
																																							n.status
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
																														: (u(),
																														  w(
																																H,
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
																							],
																						),
																						a(
																							b,
																							{
																								title: "Shift and Calendar",
																								"readonly-label":
																									"HR-owned",
																							},
																							{
																								default:
																									o(
																										() => {
																											var n;
																											return [
																												r(
																													"dl",
																													va,
																													[
																														a(
																															d,
																															{
																																label: "Assigned shift",
																																value:
																																	(n =
																																		e
																																			.value
																																			.time
																																			.shift) ==
																																	null
																																		? void 0
																																		: n.name,
																																locked: "",
																															},
																															null,
																															8,
																															[
																																"value",
																															],
																														),
																														a(
																															d,
																															{
																																label: "Timing",
																																value: m(
																																	Ae,
																																)(
																																	e
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
																														a(
																															d,
																															{
																																label: "Weekly off",
																																value: e
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
																														a(
																															d,
																															{
																																label: "Holiday list",
																																value: e
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
																	        ]))
																	      : (u(),
																	        g("div", pa, [
																						a(
																							b,
																							{
																								title: "My Documents",
																								padded: !1,
																							},
																							{
																								default:
																									o(
																										() => [
																											a(
																												Z,
																												{
																													columns:
																														M,
																													rows: e
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
																														o(
																															({
																																row: n,
																															}) => [
																																P(
																																	E(
																																		m(
																																			j,
																																		)(
																																			n.modified,
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
																						a(
																							b,
																							{
																								title: "From the Company",
																							},
																							{
																								action: o(
																									() => [
																										a(
																											m(
																												C,
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
																								default:
																									o(
																										() => [
																											a(
																												H,
																												{
																													message:
																														"Company-wide policies and handbooks live under Documents.",
																												},
																											),
																										],
																									),
																								_: 1,
																							},
																						),
																	        ])),
															]),
															_: 1,
														},
														8,
														["modelValue"],
													),
													a(
														We,
														{
															open: i.value,
															"onUpdate:open":
																t[9] ||
																(t[9] = (_) => (i.value = _)),
															title: L.value.title,
															fields: L.value.fields,
															values: te.value,
															onSaved:
																t[10] ||
																(t[10] = (_) => m(O).reload()),
														},
														null,
														8,
														["open", "title", "fields", "values"],
													),
												],
												64,
										  ))
										: V("", !0),
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
export { Ea as default };
