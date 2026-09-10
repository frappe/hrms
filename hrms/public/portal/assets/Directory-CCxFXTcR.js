import { a as V, _ as C, b as L } from "./SectionCard-C5Qs8pBJ.js";
import { _ as w } from "./StatusBadge-sSVuNJEI.js";
import { _ as B } from "./EmptyState-38_uLDf3.js";
import { k as d } from "./index-BSaIzYPn.js";
import {
	L as D,
	o as r,
	d as v,
	w as n,
	f as o,
	g as i,
	I as N,
	k as A,
	e as u,
	J as q,
	V as F,
	h as y,
	F as O,
	i as R,
	n as S,
	t as $,
	a as b,
	B as k,
	q as U,
} from "./frappe-ui-D0k6koYp.js";
const W = { class: "flex flex-col gap-3" },
	z = { class: "scroll-x pb-1" },
	E = { key: 0, class: "grid grid-cols-1 gap-3 sm:grid-cols-2" },
	I = { class: "min-w-0 flex-1" },
	J = { class: "truncate text-base-semibold text-ink-gray-9" },
	M = { class: "truncate text-sm text-ink-gray-5" },
	P = {
		__name: "Directory",
		setup(T) {
			const m = k(""),
				f = k("all"),
				c = b(() => d.data),
				x = b(() => {
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
				D(() => d.fetch()),
				(t, a) => {
					const s = U("RouterLink");
					return (
						r(),
						v(
							L,
							{ loading: i(d).loading && !i(d).data },
							{
								default: n(() => {
									var l;
									return [
										o(
											V,
											{
												title: "Directory",
												subtitle: `${_.value.length} of ${
													((l = c.value) == null ? void 0 : l.total) || 0
												} people`,
											},
											{
												actions: n(() => [
													o(
														i(N),
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
																		A("Open Org Chart", -1),
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
										u("div", W, [
											o(
												i(q),
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
											u("div", z, [
												o(
													i(F),
													{
														modelValue: f.value,
														"onUpdate:modelValue":
															a[2] || (a[2] = (e) => (f.value = e)),
														options: x.value,
													},
													null,
													8,
													["modelValue", "options"],
												),
											]),
										]),
										_.value.length
											? (r(),
											  y("div", E, [
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
																		class: "flex items-center gap-3 rounded-6 border border-outline-gray-1 bg-surface-base p-3 transition-colors hover:bg-surface-gray-1",
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
																			u("div", I, [
																				u(
																					"div",
																					J,
																					$(
																						e.employee_name,
																					),
																					1,
																				),
																				u(
																					"div",
																					M,
																					$(
																						e.designation ||
																							"—",
																					),
																					1,
																				),
																			]),
																			o(
																				w,
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
													C,
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
export { P as default };
