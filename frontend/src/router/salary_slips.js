const routes = [
	{
		path: "/salary-slip/:id",
		name: "SalarySlipDetailView",
		props: true,
		component: () => import("@/views/salary_slip/Detail.vue"),
	},
]

export default routes
