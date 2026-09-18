import {
	L,
	v as j,
	o as i,
	e as r,
	w as n,
	i as f,
	f as m,
	h as u,
	I as y,
	l as b,
	z as d,
	g as p,
	F as k,
	j as N,
	p as R,
	t as T,
	u as V,
	a as c,
	d as z,
} from "./frappe-ui-CXkWuvNK.js";
import { a as D, _ as $, b as E } from "./SectionCard-BKeIA1B1.js";
import { _ as O } from "./IdentityBand-DFaFZaDc.js";
import { _ as F } from "./PersonRow-BtXbdUjH.js";
import { q as v, d as x } from "./index-BpEXs0_U.js";
import "./StatusBadge-DcMGXIA6.js";
const q = { class: "grid items-start gap-3.5 lg:grid-cols-2" },
	I = { class: "text-base text-ink-gray-5" },
	J = { class: "flex flex-wrap gap-1.5" },
	K = {
		__name: "Colleague",
		setup(M) {
			const _ = V(),
				l = c(() => v.data),
				t = c(() => {
					var a;
					return (a = l.value) == null ? void 0 : a.employee;
				}),
				h = c(() => {
					var a, e, s;
					return [
						(a = t.value) == null ? void 0 : a.designation,
						(e = t.value) == null ? void 0 : e.department,
						(s = t.value) == null ? void 0 : s.branch,
					]
						.filter(Boolean)
						.join(" · ");
				}),
				C = c(() => {
					var e;
					const a = (e = l.value) == null ? void 0 : e.availability;
					return a
						? [
								{
									tone: a.status === "On leave" ? "on leave" : "available",
									label: a.until ? `On leave until ${x(a.until)}` : a.status,
								},
						  ]
						: [];
				}),
				w = c(() => {
					var a, e, s, o;
					return [
						{
							label: "Work Email",
							value: (a = t.value) == null ? void 0 : a.company_email,
						},
						{
							label: "Joined",
							value:
								(e = t.value) != null && e.date_of_joining
									? x(t.value.date_of_joining)
									: null,
						},
						{ label: "Tenure", value: (s = t.value) == null ? void 0 : s.tenure },
						{ label: "Location", value: (o = t.value) == null ? void 0 : o.branch },
					];
				});
			function B() {
				window.location.href = `mailto:${t.value.company_email}`;
			}
			function g() {
				v.fetch({ employee: _.params.employee });
			}
			return (
				L(g),
				j(() => _.params.employee, g),
				(a, e) => {
					const s = z("RouterLink");
					return (
						i(),
						r(
							E,
							{ loading: u(v).loading && !u(v).data },
							{
								default: n(() => [
									t.value
										? (i(),
										  f(
												k,
												{ key: 0 },
												[
													m(
														D,
														{
															crumbs: [
																{
																	label: "Directory",
																	to: "/directory",
																},
																{ label: t.value.employee_name },
															],
														},
														null,
														8,
														["crumbs"],
													),
													m(
														O,
														{
															name: t.value.employee_name,
															image: t.value.image,
															meta: h.value,
															badges: C.value,
															facts: w.value,
														},
														{
															actions: n(() => [
																t.value.company_email
																	? (i(),
																	  r(
																			u(y),
																			{
																				key: 0,
																				variant: "subtle",
																				onClick: B,
																			},
																			{
																				default: n(() => [
																					...(e[1] ||
																						(e[1] = [
																							b(
																								"Email",
																								-1,
																							),
																						])),
																				]),
																				_: 1,
																			},
																	  ))
																	: d("", !0),
																m(
																	u(y),
																	{
																		variant: "subtle",
																		onClick:
																			e[0] ||
																			(e[0] = (o) =>
																				a.$router.push(
																					"/org-chart",
																				)),
																	},
																	{
																		default: n(() => [
																			...(e[2] ||
																				(e[2] = [
																					b(
																						"Org Chart",
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
													p("div", q, [
														l.value.manager
															? (i(),
															  r(
																	$,
																	{
																		key: 0,
																		title: "Reports To",
																	},
																	{
																		default: n(() => [
																			m(
																				F,
																				{
																					name: l.value
																						.manager
																						.employee_name,
																					image: l.value
																						.manager
																						.image,
																					meta: l.value
																						.manager
																						.designation,
																					to: `/directory/${l.value.manager.name}`,
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
																			),
																		]),
																		_: 1,
																	},
															  ))
															: d("", !0),
														l.value.reports.length
															? (i(),
															  r(
																	$,
																	{ key: 1, title: "Team" },
																	{
																		action: n(() => [
																			p(
																				"span",
																				I,
																				T(
																					l.value.reports
																						.length,
																				) +
																					" direct reports ",
																				1,
																			),
																		]),
																		default: n(() => [
																			p("div", J, [
																				(i(!0),
																				f(
																					k,
																					null,
																					N(
																						l.value
																							.reports,
																						(o) => (
																							i(),
																							r(
																								s,
																								{
																									key: o.name,
																									to: `/directory/${o.name}`,
																									title: o.employee_name,
																								},
																								{
																									default:
																										n(
																											() => [
																												m(
																													u(
																														R,
																													),
																													{
																														label: o.employee_name,
																														image: o.image,
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
																			]),
																		]),
																		_: 1,
																	},
															  ))
															: d("", !0),
													]),
													e[3] ||
														(e[3] = p(
															"p",
															{ class: "text-base text-ink-gray-5" },
															" Personal, pay and document sections are not part of a colleague's profile. ",
															-1,
														)),
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
					);
				}
			);
		},
	};
export { K as default };
