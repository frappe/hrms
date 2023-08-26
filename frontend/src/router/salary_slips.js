const routes = [
	{
		path: "/salary-slip/dashboard",
		name: "SalarySlips",
		component: () => import("@/views/salary_slip/Dashboard.vue"),
	},
	{
		path: "/salary-slip/:id",
		name: "SalarySlipDetailView",
		props: true,
		component: () => import("@/views/salary_slip/Detail.vue"),
	},
]

export default routes
