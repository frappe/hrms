import {
	o as a,
	s as n,
	k as o,
	x as i,
	f as c,
	i as l,
	M as r,
	C as m,
} from "./frappe-ui-BQ9PgXrr.js";
const g = { class: "flex flex-col items-start gap-1.5 py-2" },
	f = { class: "text-base text-ink-gray-5" },
	u = {
		__name: "EmptyState",
		props: { message: String, action: String },
		emits: ["action"],
		setup(e) {
			return (s, t) => (
				a(),
				n("div", g, [
					o("p", f, i(e.message), 1),
					e.action
						? (a(),
						  c(
								l(r),
								{
									key: 0,
									class: "-ml-2",
									variant: "ghost",
									label: e.action,
									onClick: t[0] || (t[0] = (k) => s.$emit("action")),
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
export { u as _ };
