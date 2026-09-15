import {
	o as t,
	e as o,
	w as l,
	f as r,
	h as c,
	p as m,
	g as a,
	s,
	t as n,
	i as g,
	z as d,
	Y as u,
	a2 as f,
} from "./frappe-ui-CXkWuvNK.js";
const h = { class: "min-w-0 leading-tight" },
	k = { key: 0, class: "truncate text-base text-ink-gray-5" },
	v = {
		__name: "PersonRow",
		props: {
			name: String,
			image: String,
			meta: String,
			to: [String, Object],
			size: { type: String, default: "lg" },
		},
		setup(e) {
			return (i, x) => (
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
							a("div", h, [
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
								e.meta ? (t(), g("div", k, n(e.meta), 1)) : d("", !0),
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
export { v as _ };
