import { o as a, h as n, e as t, t as s, s as o } from "./frappe-ui-D0k6koYp.js";
const r = {
		class: "flex items-baseline justify-between gap-3 border-t border-outline-gray-2 px-3.5 py-2.5",
	},
	l = { class: "text-base text-ink-gray-5" },
	g = {
		__name: "TotalRow",
		props: { label: String, value: [String, Number], strong: Boolean },
		setup(e) {
			return (i, c) => (
				a(),
				n("div", r, [
					t("span", l, s(e.label), 1),
					t(
						"span",
						{
							class: o([
								"nums shrink-0 font-semibold text-ink-gray-9",
								e.strong ? "text-lg" : "text-base",
							]),
						},
						s(e.value),
						3,
					),
				])
			);
		},
	};
export { g as _ };
