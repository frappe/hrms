import {
	o as s,
	s as a,
	F as i,
	t as d,
	k as l,
	x as t,
	f as u,
	i as g,
	a1 as m,
	C as n,
	v as p,
	a as _,
} from "./frappe-ui-BQ9PgXrr.js";
const x = { class: "text-base text-ink-gray-5" },
	f = { class: "nums text-xl font-semibold leading-tight text-ink-gray-9" },
	k = { key: 1, class: "mt-0.5 text-sm text-ink-gray-5" },
	v = {
		__name: "StatTiles",
		props: { tiles: { type: Array, default: () => [] } },
		setup(r) {
			const o = r,
				c = _(() =>
					o.tiles.length === 3
						? "grid-cols-1 sm:grid-cols-3"
						: "grid-cols-2 lg:grid-cols-4",
				);
			return (y, h) => (
				s(),
				a(
					"div",
					{ class: p(["grid gap-3", c.value]) },
					[
						(s(!0),
						a(
							i,
							null,
							d(
								r.tiles,
								(e) => (
									s(),
									a(
										"div",
										{
											key: e.label,
											class: "flex flex-col gap-0.5 rounded-lg border border-outline-gray-1 bg-surface-white p-3",
										},
										[
											l("span", x, t(e.label), 1),
											l("span", f, t(e.value), 1),
											e.pct !== void 0
												? (s(),
												  u(
														g(m),
														{
															key: 0,
															class: "mt-1.5",
															value: e.pct,
															size: "md",
														},
														null,
														8,
														["value"],
												  ))
												: n("", !0),
											e.hint ? (s(), a("span", k, t(e.hint), 1)) : n("", !0),
										],
									)
								),
							),
							128,
						)),
					],
					2,
				)
			);
		},
	};
export { v as _ };
