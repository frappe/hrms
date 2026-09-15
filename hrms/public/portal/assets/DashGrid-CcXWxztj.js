import { o as l, i as t, g as e, Y as a, s as c, a as n } from "./frappe-ui-CXkWuvNK.js";
const d = { class: "flex min-w-0 flex-col gap-3.5" },
	m = { class: "flex min-w-0 flex-col gap-3.5" },
	_ = {
		__name: "DashGrid",
		props: { ratio: { type: String, default: "wide" } },
		setup(o) {
			const i = o,
				r = n(() =>
					i.ratio === "even"
						? "grid-cols-1 lg:grid-cols-2"
						: "grid-cols-1 lg:grid-cols-[minmax(0,1.6fr)_minmax(0,1fr)]",
				);
			return (s, g) => (
				l(),
				t(
					"div",
					{ class: c(["grid items-start gap-3.5", r.value]) },
					[e("div", d, [a(s.$slots, "main")]), e("div", m, [a(s.$slots, "side")])],
					2,
				)
			);
		},
	};
export { _ };
