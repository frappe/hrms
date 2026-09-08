import {
	o as t,
	f as o,
	g as l,
	h as r,
	i as c,
	j as m,
	k as a,
	v as s,
	x as n,
	s as g,
	C as d,
	a2 as u,
	a6 as f,
} from "./frappe-ui-BQ9PgXrr.js";
const k = { class: "min-w-0 leading-tight" },
	x = { key: 0, class: "truncate text-base text-ink-gray-5" },
	S = {
		__name: "PersonRow",
		props: {
			name: String,
			image: String,
			meta: String,
			to: [String, Object],
			size: { type: String, default: "lg" },
		},
		setup(e) {
			return (i, h) => (
				t(),
				o(
					f(e.to ? "RouterLink" : "div"),
					{ to: e.to, class: s(["flex min-w-0 items-center gap-2.5", e.to && "group"]) },
					{
						default: l(() => [
							r(c(m), { label: e.name, image: e.image, size: e.size }, null, 8, [
								"label",
								"image",
								"size",
							]),
							a("div", k, [
								a(
									"div",
									{
										class: s([
											"truncate text-p-base text-ink-gray-9",
											e.to && "group-hover:underline",
										]),
									},
									n(e.name),
									3,
								),
								e.meta ? (t(), g("div", x, n(e.meta), 1)) : d("", !0),
							]),
							u(i.$slots, "default"),
						]),
						_: 3,
					},
					8,
					["to", "class"],
				)
			);
		},
	};
export { S as _ };
