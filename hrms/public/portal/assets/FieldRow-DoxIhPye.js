import {
	o as a,
	h as t,
	e as l,
	t as n,
	X as u,
	s as o,
	z as m,
	a as i,
} from "./frappe-ui-D0k6koYp.js";
const k = {
		class: "grid gap-x-3 gap-y-0.5 border-b border-outline-gray-1 py-1.5 last:border-0 last:pb-0 first:pt-0 sm:grid-cols-[7.5rem_minmax(0,1fr)] sm:items-baseline",
	},
	g = { class: "text-base text-ink-gray-5" },
	p = { key: 0, class: "italic text-ink-gray-4" },
	y = {
		key: 0,
		class: "lucide-lock ml-1 inline-block size-3 shrink-0 align-[-1px] text-ink-gray-4",
		"aria-hidden": "true",
	},
	v = {
		__name: "FieldRow",
		props: { label: String, value: [String, Number], locked: Boolean, nums: Boolean },
		setup(e) {
			const s = e,
				r = i(() => s.value === null || s.value === void 0 || s.value === ""),
				c = i(() => (s.locked ? "text-ink-gray-7" : "text-ink-gray-8"));
			return (d, b) => (
				a(),
				t("div", k, [
					l("dt", g, n(e.label), 1),
					l(
						"dd",
						{ class: o(["min-w-0 text-p-base", c.value]) },
						[
							u(d.$slots, "default", {}, () => [
								r.value
									? (a(), t("span", p, "Not set"))
									: (a(),
									  t(
											"span",
											{ key: 1, class: o(e.nums && "nums") },
											n(e.value),
											3,
									  )),
							]),
							e.locked ? (a(), t("span", y)) : m("", !0),
						],
						2,
					),
				])
			);
		},
	};
export { v as _ };
