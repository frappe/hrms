import {
	o as l,
	s as a,
	k as i,
	F as c,
	t as o,
	v as d,
	x as y,
	a2 as b,
	B as g,
	a7 as B,
	a8 as N,
	C as p,
	h as S,
	a as v,
} from "./frappe-ui-BQ9PgXrr.js";
import { _ as V } from "./EmptyState-DNwecFw5.js";
const _ = { class: "scroll-x hidden md:block" },
	D = { class: "w-full border-collapse" },
	K = ["onClick"],
	M = { class: "md:hidden" },
	A = ["onClick"],
	F = { class: "min-w-0" },
	T = { class: "text-p-base text-ink-gray-8" },
	j = { class: "mt-0.5 flex flex-wrap items-center gap-x-2 text-base text-ink-gray-5" },
	z = { key: 0, class: "shrink-0" },
	E = { key: 0, class: "px-3.5 pb-3.5" },
	q = {
		__name: "DataTable",
		props: {
			columns: { type: Array, default: () => [] },
			rows: { type: Array, default: () => [] },
			emptyMessage: { type: String, default: "Nothing here yet." },
			clickable: Boolean,
			idKey: { type: String, default: "name" },
		},
		emits: ["row-click"],
		setup(n) {
			const u = n,
				h = v(() => u.columns.find((t) => t.primary) || u.columns[0] || { key: "" }),
				m = v(() => u.columns.find((t) => t.badge)),
				$ = v(() =>
					u.columns.filter((t) => t !== h.value && t !== m.value && !t.hideOnMobile),
				);
			function x(t, r) {
				var e;
				return (e = t == null ? void 0 : t[u.idKey]) != null ? e : r;
			}
			function k(t, r) {
				const e = t == null ? void 0 : t[r.key];
				return e == null || e === "" ? "—" : e;
			}
			function C(t, r) {
				const e = t == null ? void 0 : t[r.key];
				return e != null && e !== "";
			}
			return (t, r) => (
				l(),
				a("div", null, [
					i("div", _, [
						i("table", D, [
							i("thead", null, [
								i("tr", null, [
									(l(!0),
									a(
										c,
										null,
										o(
											n.columns,
											(e) => (
												l(),
												a(
													"th",
													{
														key: e.key,
														class: d([
															"whitespace-nowrap border-b border-outline-gray-1 px-3.5 py-2 text-base font-medium text-ink-gray-5",
															e.align === "right"
																? "text-right"
																: "text-left",
														]),
													},
													y(e.label),
													3,
												)
											),
										),
										128,
									)),
								]),
							]),
							i("tbody", null, [
								(l(!0),
								a(
									c,
									null,
									o(
										n.rows,
										(e, f) => (
											l(),
											a(
												"tr",
												{
													key: x(e, f),
													class: d([
														"border-b border-outline-gray-1 last:border-0",
														n.clickable &&
															"cursor-pointer hover:bg-surface-gray-1",
													]),
													onClick: (s) =>
														n.clickable && t.$emit("row-click", e),
												},
												[
													(l(!0),
													a(
														c,
														null,
														o(
															n.columns,
															(s) => (
																l(),
																a(
																	"td",
																	{
																		key: s.key,
																		class: d([
																			"px-3.5 py-2.5 text-p-base text-ink-gray-8",
																			[
																				s.align === "right"
																					? "text-right"
																					: "text-left",
																				s.nums && "nums",
																				s.muted &&
																					"text-ink-gray-5",
																				s.strong &&
																					"font-semibold text-ink-gray-9",
																			],
																		]),
																	},
																	[
																		b(
																			t.$slots,
																			`cell-${s.key}`,
																			{ row: e },
																			() => [
																				g(y(k(e, s)), 1),
																			],
																		),
																	],
																	2,
																)
															),
														),
														128,
													)),
												],
												10,
												K,
											)
										),
									),
									128,
								)),
							]),
						]),
					]),
					i("ul", M, [
						(l(!0),
						a(
							c,
							null,
							o(
								n.rows,
								(e, f) => (
									l(),
									a(
										"li",
										{
											key: x(e, f),
											class: d([
												"flex items-start justify-between gap-3 border-b border-outline-gray-1 px-3.5 py-2.5 last:border-0",
												n.clickable && "cursor-pointer",
											]),
											onClick: (s) => n.clickable && t.$emit("row-click", e),
										},
										[
											i("div", F, [
												i("div", T, [
													b(
														t.$slots,
														`cell-${h.value.key}`,
														{ row: e },
														() => [g(y(k(e, h.value)), 1)],
													),
												]),
												i("div", j, [
													(l(!0),
													a(
														c,
														null,
														o($.value, (s) =>
															B(
																(l(),
																a(
																	"span",
																	{
																		key: s.key,
																		class: d(s.nums && "nums"),
																	},
																	[
																		b(
																			t.$slots,
																			`cell-${s.key}`,
																			{ row: e },
																			() => [
																				g(y(k(e, s)), 1),
																			],
																		),
																	],
																	2,
																)),
																[[N, C(e, s)]],
															),
														),
														128,
													)),
												]),
											]),
											m.value
												? (l(),
												  a("div", z, [
														b(
															t.$slots,
															`cell-${m.value.key}`,
															{ row: e },
															() => [g(y(k(e, m.value)), 1)],
														),
												  ]))
												: p("", !0),
										],
										10,
										A,
									)
								),
							),
							128,
						)),
					]),
					n.rows.length
						? p("", !0)
						: (l(),
						  a("div", E, [S(V, { message: n.emptyMessage }, null, 8, ["message"])])),
				])
			);
		},
	};
export { q as _ };
