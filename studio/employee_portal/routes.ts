// Page routes, relative to the app route
export const ROUTES = {
	home: "/",
	inbox: "/inbox",
	news: "/news",
	people: "/people",
	policies: "/policies",
	attendance: "/attendance",
	applyLeave: "/attendance/leave/new",
	pay: "/pay",
	expenses: "/expenses",
	newExpenseClaim: "/expenses/new",
	performance: "/performance",
	offboarding: "/offboarding",
	firstMonth: "/onboarding",
	joiners: "/onboarding/joiners",
	profile: "/profile",
};

export const inboxItem = (id: string) => ({
	path: ROUTES.inbox,
	query: { tab: "todo", item: id },
});
