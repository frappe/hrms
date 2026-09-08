import { _ as c } from "./EmptyState-DNwecFw5.js";
import {
	o as a,
	s as l,
	F as o,
	t as i,
	f as n,
	g as m,
	k as _,
	x as r,
	i as f,
	a1 as p,
	C as u,
} from "./frappe-ui-BQ9PgXrr.js";
const d = { class: "flex flex-col gap-3" },
	x = { class: "nums text-base font-medium text-ink-gray-5" },
	v = {
		__name: "BalanceBars",
		props: { balances: { type: Array, default: () => [] } },
		setup(t) {
			return (y, g) => {
				var s;
				return (
					a(),
					l("div", d, [
						(a(!0),
						l(
							o,
							null,
							i(
								t.balances,
								(e) => (
									a(),
									n(
										f(p),
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
													x,
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
