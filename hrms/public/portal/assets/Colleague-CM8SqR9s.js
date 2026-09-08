import {
	u as j,
	P as L,
	w as N,
	q as R,
	o as i,
	f as r,
	g as n,
	s as f,
	F as y,
	h as m,
	i as u,
	M as b,
	B as k,
	C as d,
	k as p,
	t as T,
	j as V,
	x as D,
	a as c,
} from "./frappe-ui-BQ9PgXrr.js";
import { _ as $, a as E } from "./SectionCard-u_7VCKnT.js";
import { _ as O } from "./PageHead-3jtDpZ9g.js";
import { _ as z } from "./IdentityBand-BGB1Buc7.js";
import { _ as F } from "./PersonRow-DZ4YBxpS.js";
import { n as _, d as x } from "./index-DKSqIuAQ.js";
import "./StatusBadge-Bqz4zlkD.js";
const M = { class: "grid items-start gap-3.5 lg:grid-cols-2" },
	P = { class: "text-base text-ink-gray-5" },
	q = { class: "flex flex-wrap gap-1.5" },
	Q = {
		__name: "Colleague",
		setup(J) {
			const g = j(),
				l = c(() => _.data),
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
			function v() {
				_.fetch({ employee: g.params.employee });
			}
			return (
				L(v),
				N(() => g.params.employee, v),
				(a, e) => {
					const s = R("RouterLink");
					return (
						i(),
						r(
							E,
							{ loading: u(_).loading && !u(_).data },
							{
								default: n(() => [
									t.value
										? (i(),
										  f(
												y,
												{ key: 0 },
												[
													m(
														O,
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
														z,
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
																			u(b),
																			{
																				key: 0,
																				variant: "subtle",
																				onClick: B,
																			},
																			{
																				default: n(() => [
																					...(e[1] ||
																						(e[1] = [
																							k(
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
																	u(b),
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
																					k(
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
													p("div", M, [
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
																				P,
																				D(
																					l.value.reports
																						.length,
																				) +
																					" direct reports ",
																				1,
																			),
																		]),
																		default: n(() => [
																			p("div", q, [
																				(i(!0),
																				f(
																					y,
																					null,
																					T(
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
																														V,
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
export { Q as default };
