import {
	o as t,
	d as o,
	w as l,
	f as r,
	g as c,
	n as m,
	e as a,
	s as n,
	t as s,
	h as g,
	z as d,
	Y as u,
	a2 as f,
} from "./frappe-ui-rHlwnvVy.js";
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
					{ to: e.to, class: n(["flex min-w-0 items-center gap-2.5", e.to && "group"]) },
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
										class: n([
											"truncate text-p-base text-ink-gray-9",
											e.to && "group-hover:underline",
										]),
									},
									s(e.name),
									3,
								),
								e.meta ? (t(), g("div", k, s(e.meta), 1)) : d("", !0),
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
