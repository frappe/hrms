import { createRouter, createWebHistory } from "vue-router";

const routes = [
	{ path: "/", redirect: "/home" },
	{ path: "/home", name: "Home", component: () => import("@/pages/Home.vue") },
	{
		path: "/attendance",
		name: "Attendance",
		component: () => import("@/pages/Attendance.vue"),
	},
	{ path: "/leave", name: "Leave", component: () => import("@/pages/Leave.vue") },
	{ path: "/expenses", name: "Expenses", component: () => import("@/pages/Expenses.vue") },
	// every employee-raised document is viewed and edited through one page
	{
		path: "/requests/:type/:name",
		name: "Request",
		component: () => import("@/pages/Request.vue"),
	},
	{ path: "/expenses/:name", redirect: (to) => `/requests/expense/${to.params.name}` },
	{ path: "/payslips", name: "Payslips", component: () => import("@/pages/Payslips.vue") },
	// a payslip is read-only, so it gets its own page rather than the request one
	{ path: "/payslips/:name", name: "Payslip", component: () => import("@/pages/Payslip.vue") },
	{ path: "/advances", name: "Advances", component: () => import("@/pages/Advances.vue") },
	{
		path: "/appraisals",
		name: "Appraisals",
		component: () => import("@/pages/Appraisals.vue"),
	},
	// an appraisal is read-only in the portal, like a payslip
	{
		path: "/appraisals/:name",
		name: "Appraisal",
		component: () => import("@/pages/Appraisal.vue"),
	},
	{ path: "/directory", name: "Directory", component: () => import("@/pages/Directory.vue") },
	{
		path: "/directory/:employee",
		name: "Colleague",
		component: () => import("@/pages/Colleague.vue"),
	},
	{ path: "/org-chart", name: "OrgChart", component: () => import("@/pages/OrgChart.vue") },
	{ path: "/holidays", name: "Holidays", component: () => import("@/pages/Holidays.vue") },
	{ path: "/documents", name: "Documents", component: () => import("@/pages/Documents.vue") },
	{ path: "/me", name: "Profile", component: () => import("@/pages/Profile.vue") },
	// screens contributed by regional/custom apps, rendered from their own spec
	{ path: "/x/:slug", name: "Extension", component: () => import("@/pages/Extension.vue") },
	{ path: "/:pathMatch(.*)*", redirect: "/home" },
];

const router = createRouter({
	history: createWebHistory("/hrms"),
	routes,
	scrollBehavior: () => ({ top: 0 }),
});

export default router;
