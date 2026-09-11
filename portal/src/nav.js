export const NAV = [
	{
		group: "My Work",
		items: [
			{ label: "Home", to: "/home", icon: "lucide-home" },
			{ label: "Attendance", to: "/attendance", icon: "lucide-clock" },
			{ label: "Leave", to: "/leave", icon: "lucide-sunrise" },
			{
				label: "Expenses",
				to: "/expenses",
				icon: "lucide-credit-card",
				countKey: "expenses",
			},
			{ label: "Payslips", to: "/payslips", icon: "lucide-file-text" },
			{ label: "Advances", to: "/advances", icon: "lucide-trending-up" },
			{ label: "Appraisals", to: "/appraisals", icon: "lucide-award" },
		],
	},
	{
		group: "Company",
		items: [
			{ label: "Directory", to: "/directory", icon: "lucide-users" },
			{ label: "Org chart", to: "/org-chart", icon: "lucide-git-merge" },
			{ label: "Holidays", to: "/holidays", icon: "lucide-calendar" },
			{ label: "Documents", to: "/documents", icon: "lucide-folder" },
		],
	},
];

/**
 * Five bottom-tab slots below md. Everything else stays reachable through the
 * drawer, so nothing is removed, only relocated.
 */
export const TABS = [
	{ label: "Home", to: "/home", icon: "lucide-home" },
	{ label: "Attendance", to: "/attendance", icon: "lucide-clock" },
	{ label: "Leave", to: "/leave", icon: "lucide-sunrise" },
	{ label: "Pay", to: "/payslips", icon: "lucide-file-text" },
	// opens the drawer rather than routing: it is the only way to reach the
	// Company group and the profile now that there is no top bar
	{ label: "More", action: "more", icon: "lucide-menu" },
];
