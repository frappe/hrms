import { _ as c } from "./EmptyState-38_uLDf3.js";
import {
	o as a,
	h as l,
	F as o,
	i,
	d as n,
	w as m,
	e as _,
	t as r,
	g as d,
	a1 as p,
	z as u,
} from "./frappe-ui-D0k6koYp.js";
const f = { class: "flex flex-col gap-3" },
	h = { class: "nums text-base-medium text-ink-gray-5" },
	v = {
		__name: "BalanceBars",
		props: { balances: { type: Array, default: () => [] } },
		setup(t) {
			return (y, g) => {
				var s;
				return (
					a(),
					l("div", f, [
						(a(!0),
						l(
							o,
							null,
							i(
								t.balances,
								(e) => (
									a(),
									n(
										d(p),
										{
											key: e.leave_type,
											value: e.pct,
											size: "md",
											label: e.leave_type,
										},
										{
											hint: m(() => [
												_(
													"span",
													h,
													r(e.balance) + " of " + r(e.allocated),
													1,
												),
											]),
											_: 2,
										},
										1032,
										["value", "label"],
									)
								),
							),
							128,
						)),
						(s = t.balances) != null && s.length
							? u("", !0)
							: (a(),
							  n(c, { key: 0, message: "No leave allocated for this period." })),
					])
				);
			};
		},
	};
export { v as _ };
