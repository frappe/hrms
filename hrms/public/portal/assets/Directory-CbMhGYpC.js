import { _ as V, a as C } from "./SectionCard-u_7VCKnT.js";
import { _ as w } from "./PageHead-3jtDpZ9g.js";
import { _ as L } from "./StatusBadge-Bqz4zlkD.js";
import { _ as B } from "./EmptyState-DNwecFw5.js";
import { k as d } from "./index-DKSqIuAQ.js";
import {
	P as N,
	q as D,
	o as r,
	f as v,
	g as n,
	h as o,
	i,
	M as A,
	B as q,
	k as u,
	N as F,
	Z as M,
	s as y,
	F as O,
	t as R,
	j as S,
	x,
	a as b,
	e as $,
} from "./frappe-ui-BQ9PgXrr.js";
const U = { class: "flex flex-col gap-3" },
	W = { class: "scroll-x pb-1" },
	j = { key: 0, class: "grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3" },
	z = { class: "min-w-0 flex-1" },
	E = { class: "truncate text-base font-semibold text-ink-gray-9" },
	P = { class: "truncate text-sm text-ink-gray-5" },
	K = {
		__name: "Directory",
		setup(T) {
			const m = $(""),
				f = $("all"),
				c = b(() => d.data),
				k = b(() => {
					var a, s;
					const t = [
						{ value: "all", label: "All" },
						{ value: "available", label: "Available today" },
					];
					for (const l of ((a = c.value) == null ? void 0 : a.departments) || [])
						t.push({ value: `dept:${l}`, label: l });
					for (const l of ((s = c.value) == null ? void 0 : s.branches) || [])
						t.push({ value: `branch:${l}`, label: l });
					return t;
				}),
				_ = b(() => {
					var l;
					let t = ((l = c.value) == null ? void 0 : l.people) || [];
					const a = m.value.trim().toLowerCase();
					a &&
						(t = t.filter((e) => {
							var p, g, h;
							return (
								((p = e.employee_name) == null
									? void 0
									: p.toLowerCase().includes(a)) ||
								((g = e.designation) == null
									? void 0
									: g.toLowerCase().includes(a)) ||
								((h = e.department) == null ? void 0 : h.toLowerCase().includes(a))
							);
						}));
					const s = f.value;
					return (
						s === "available"
							? (t = t.filter((e) => e.availability === "Available"))
							: s.startsWith("dept:")
							  ? (t = t.filter((e) => e.department === s.slice(5)))
							  : s.startsWith("branch:") &&
							    (t = t.filter((e) => e.branch === s.slice(7))),
						t
					);
				});
			return (
				N(() => d.fetch()),
				(t, a) => {
					const s = D("RouterLink");
					return (
						r(),
						v(
							C,
							{ loading: i(d).loading && !i(d).data },
							{
								default: n(() => {
									var l;
									return [
										o(
											w,
											{
												title: "Directory",
												subtitle: `${_.value.length} of ${
													((l = c.value) == null ? void 0 : l.total) || 0
												} people`,
											},
											{
												actions: n(() => [
													o(
														i(A),
														{
															variant: "subtle",
															onClick:
																a[0] ||
																(a[0] = (e) =>
																	t.$router.push("/org-chart")),
														},
														{
															default: n(() => [
																...(a[3] ||
																	(a[3] = [
																		q("Open Org Chart", -1),
																	])),
															]),
															_: 1,
														},
													),
												]),
												_: 1,
											},
											8,
											["subtitle"],
										),
										u("div", U, [
											o(
												i(F),
												{
													modelValue: m.value,
													"onUpdate:modelValue":
														a[1] || (a[1] = (e) => (m.value = e)),
													type: "text",
													placeholder: "Search by name or role",
													autocomplete: "off",
												},
												null,
												8,
												["modelValue"],
											),
											u("div", W, [
												o(
													i(M),
													{
														modelValue: f.value,
														"onUpdate:modelValue":
															a[2] || (a[2] = (e) => (f.value = e)),
														buttons: k.value,
													},
													null,
													8,
													["modelValue", "buttons"],
												),
											]),
										]),
										_.value.length
											? (r(),
											  y("div", j, [
													(r(!0),
													y(
														O,
														null,
														R(
															_.value,
															(e) => (
																r(),
																v(
																	s,
																	{
																		key: e.name,
																		to: `/directory/${e.name}`,
																		class: "flex items-center gap-3 rounded-lg border border-outline-gray-1 bg-surface-white p-3 transition-colors hover:bg-surface-gray-1",
																	},
																	{
																		default: n(() => [
																			o(
																				i(S),
																				{
																					label: e.employee_name,
																					image: e.image,
																					size: "3xl",
																				},
																				null,
																				8,
																				["label", "image"],
																			),
																			u("div", z, [
																				u(
																					"div",
																					E,
																					x(
																						e.employee_name,
																					),
																					1,
																				),
																				u(
																					"div",
																					P,
																					x(
																						e.designation ||
																							"—",
																					),
																					1,
																				),
																			]),
																			o(
																				L,
																				{
																					class: "shrink-0",
																					status: e.is_self
																						? "you"
																						: e.availability,
																					label: e.is_self
																						? "You"
																						: e.availability,
																				},
																				null,
																				8,
																				[
																					"status",
																					"label",
																				],
																			),
																		]),
																		_: 2,
																	},
																	1032,
																	["to"],
																)
															),
														),
														128,
													)),
											  ]))
											: (r(),
											  v(
													V,
													{ key: 1 },
													{
														default: n(() => [
															o(B, {
																message:
																	"Nobody matches that search.",
															}),
														]),
														_: 1,
													},
											  )),
									];
								}),
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
