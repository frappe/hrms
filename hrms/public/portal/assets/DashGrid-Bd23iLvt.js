import { o as l, s as t, k as a, a2 as e, v as c, a as n } from "./frappe-ui-BQ9PgXrr.js";
const d = { class: "flex min-w-0 flex-col gap-3.5" },
	m = { class: "flex min-w-0 flex-col gap-3.5" },
	_ = {
		__name: "DashGrid",
		props: { ratio: { type: String, default: "wide" } },
		setup(o) {
			const r = o,
				i = n(() =>
					r.ratio === "even"
						? "grid-cols-1 lg:grid-cols-2"
						: "grid-cols-1 lg:grid-cols-[minmax(0,1.6fr)_minmax(0,1fr)]",
				);
			return (s, p) => (
				l(),
				t(
					"div",
					{ class: c(["grid items-start gap-3.5", i.value]) },
					[a("div", d, [e(s.$slots, "main")]), a("div", m, [e(s.$slots, "side")])],
					2,
				)
			);
		},
	};
export { _ };
