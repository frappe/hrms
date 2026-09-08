import {
	o as s,
	s as t,
	k as l,
	x as n,
	a2 as d,
	v as o,
	f as u,
	i as k,
	p as g,
	C as p,
	a as r,
} from "./frappe-ui-BQ9PgXrr.js";
const y = {
		class: "grid gap-x-3 gap-y-0.5 border-b border-outline-gray-1 py-1.5 last:border-0 last:pb-0 first:pt-0 sm:grid-cols-[7.5rem_minmax(0,1fr)] sm:items-baseline",
	},
	x = { class: "text-base text-ink-gray-5" },
	b = { key: 0, class: "italic text-ink-gray-4" },
	_ = {
		__name: "FieldRow",
		props: { label: String, value: [String, Number], locked: Boolean, nums: Boolean },
		setup(e) {
			const a = e,
				i = r(() => a.value === null || a.value === void 0 || a.value === ""),
				c = r(() => (a.locked ? "text-ink-gray-7" : "text-ink-gray-8"));
			return (m, v) => (
				s(),
				t("div", y, [
					l("dt", x, n(e.label), 1),
					l(
						"dd",
						{ class: o(["min-w-0 text-p-base", c.value]) },
						[
							d(m.$slots, "default", {}, () => [
								i.value
									? (s(), t("span", b, "Not set"))
									: (s(),
									  t(
											"span",
											{ key: 1, class: o(e.nums && "nums") },
											n(e.value),
											3,
									  )),
							]),
							e.locked
								? (s(),
								  u(k(g), {
										key: 0,
										name: "lock",
										class: "ml-1 inline h-3 w-3 shrink-0 align-[-1px] text-ink-gray-4",
								  }))
								: p("", !0),
						],
						2,
					),
				])
			);
		},
	};
export { _ };
