import {
	o as a,
	h as n,
	e as o,
	t as i,
	d as c,
	g as l,
	I as r,
	z as m,
} from "./frappe-ui-rHlwnvVy.js";
const g = { class: "flex flex-col items-start gap-1.5 py-2" },
	p = { class: "text-base text-ink-gray-5" },
	k = {
		__name: "EmptyState",
		props: { message: String, action: String },
		emits: ["action"],
		setup(e) {
			return (s, t) => (
				a(),
				n("div", g, [
					o("p", p, i(e.message), 1),
					e.action
						? (a(),
						  c(
								l(r),
								{
									key: 0,
									class: "-ml-2",
									variant: "ghost",
									label: e.action,
									onClick: t[0] || (t[0] = (d) => s.$emit("action")),
								},
								null,
								8,
								["label"],
						  ))
						: m("", !0),
				])
			);
		},
	};
export { k as _ };
