export const NAV = [
	{
		group: "My Work",
		items: [
			{ label: "Home", to: "/home", icon: "home" },
			{ label: "Attendance", to: "/attendance", icon: "clock" },
			{ label: "Leave", to: "/leave", icon: "sunrise" },
			{ label: "Expenses", to: "/expenses", icon: "credit-card", countKey: "expenses" },
			{ label: "Payslips", to: "/payslips", icon: "file-text" },
			{ label: "Advances", to: "/advances", icon: "trending-up" },
		],
	},
	{
		group: "Company",
		items: [
			{ label: "Directory", to: "/directory", icon: "users" },
			{ label: "Org chart", to: "/org-chart", icon: "git-merge" },
			{ label: "Holidays", to: "/holidays", icon: "calendar" },
			{ label: "Documents", to: "/documents", icon: "folder" },
		],
	},
];

/**
 * Five bottom-tab slots below md. Everything else stays reachable through the
 * drawer, so nothing is removed, only relocated.
 */
export const TABS = [
	{ label: "Home", to: "/home", icon: "home" },
	{ label: "Attendance", to: "/attendance", icon: "clock" },
	{ label: "Leave", to: "/leave", icon: "sunrise" },
	{ label: "Pay", to: "/payslips", icon: "file-text" },
	// opens the drawer rather than routing: it is the only way to reach the
	// Company group and the profile now that there is no top bar
	{ label: "More", action: "more", icon: "menu" },
];
