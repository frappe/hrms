import {
	o as s,
	h as a,
	F as i,
	i as d,
	e as l,
	t,
	d as u,
	g,
	O as m,
	z as n,
	s as p,
	a as _,
} from "./frappe-ui-rHlwnvVy.js";
const x = { class: "text-base text-ink-gray-5" },
	y = { class: "nums text-2xl-semibold leading-tight text-ink-gray-9" },
	f = { key: 1, class: "mt-0.5 text-sm text-ink-gray-5" },
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
			return (h, k) => (
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
											class: "flex flex-col gap-0.5 rounded-6 border border-outline-gray-1 bg-surface-base p-3",
										},
										[
											l("span", x, t(e.label), 1),
											l("span", y, t(e.value), 1),
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
											e.hint ? (s(), a("span", f, t(e.hint), 1)) : n("", !0),
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
