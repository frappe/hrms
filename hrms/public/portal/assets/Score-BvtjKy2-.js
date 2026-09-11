import { o as t, h as s, k as n, t as o, e as r, s as l } from "./frappe-ui-rHlwnvVy.js";
const c = { key: 0, class: "text-ink-gray-4" },
	k = {
		__name: "Score",
		props: { value: { type: Number, default: 0 }, strong: { type: Boolean, default: !1 } },
		setup(e) {
			return (i, a) =>
				e.value
					? (t(),
					  s(
							"span",
							{
								key: 1,
								class: l([
									"nums",
									e.strong ? "font-semibold text-ink-gray-9" : "text-ink-gray-6",
								]),
							},
							[
								n(o(e.value), 1),
								a[0] || (a[0] = r("span", { class: "text-ink-gray-4" }, "/5", -1)),
							],
							2,
					  ))
					: (t(), s("span", c, "—"));
		},
	};
export { k as _ };
