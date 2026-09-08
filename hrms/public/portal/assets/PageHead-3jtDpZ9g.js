import {
	o as s,
	s as a,
	k as c,
	f as r,
	i as m,
	a3 as u,
	C as l,
	x as n,
	a2 as d,
	a as b,
} from "./frappe-ui-BQ9PgXrr.js";
const f = { class: "flex flex-wrap items-end justify-between gap-3" },
	k = { class: "min-w-0" },
	x = { key: 1, class: "truncate text-xl font-semibold text-ink-gray-9" },
	g = { key: 2, class: "mt-0.5 text-base text-ink-gray-5" },
	y = { key: 0, class: "flex flex-wrap items-center gap-2" },
	p = {
		__name: "PageHead",
		props: { title: String, subtitle: String, crumbs: Array },
		setup(e) {
			const o = e,
				i = b(() => (o.crumbs || []).map((t) => ({ label: t.label, route: t.to })));
			return (t, _) => (
				s(),
				a("div", f, [
					c("div", k, [
						i.value.length
							? (s(),
							  r(m(u), { key: 0, class: "mb-0.5", items: i.value }, null, 8, [
									"items",
							  ]))
							: l("", !0),
						e.title ? (s(), a("h1", x, n(e.title), 1)) : l("", !0),
						e.subtitle ? (s(), a("p", g, n(e.subtitle), 1)) : l("", !0),
					]),
					t.$slots.actions ? (s(), a("div", y, [d(t.$slots, "actions")])) : l("", !0),
				])
			);
		},
	};
export { p as _ };
