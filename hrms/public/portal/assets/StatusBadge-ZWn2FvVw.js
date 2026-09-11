import { o as d, d as l, g as o, ak as c, a as u } from "./frappe-ui-rHlwnvVy.js";
const p = {
	__name: "StatusBadge",
	props: { status: String, label: String },
	setup(e) {
		const r = e,
			n = {
				green: [
					"approved",
					"present",
					"verified",
					"paid",
					"reimbursed",
					"available",
					"deducted",
					"claimed",
					"on shift",
					"work from home",
					"completed",
				],
				amber: [
					"pending",
					"open",
					"in review",
					"scheduled",
					"on leave",
					"half day",
					"unmarked",
					"awaiting",
					"due",
					"not declared",
					"withheld",
				],
				red: ["rejected", "absent", "cancelled", "expiring", "expired", "overdue"],
				blue: ["draft", "repaying", "remote", "unsubmitted", "submitted"],
				gray: [
					"taken",
					"settled",
					"closed",
					"holiday",
					"weekly off",
					"you",
					"inactive",
					"past",
				],
			},
			s = u(() => {
				const t = String(r.status || "").toLowerCase();
				for (const [a, i] of Object.entries(n)) if (i.includes(t)) return a;
				return "gray";
			});
		return (t, a) => (
			d(),
			l(
				o(c),
				{ theme: s.value, label: e.label || e.status, variant: "subtle", size: "xl" },
				null,
				8,
				["theme", "label"],
			)
		);
	},
};
export { p as _ };
