const routes = [
	{
		path: "/salary-slips/:id",
		name: "SalarySlipDetailView",
		props: true,
		component: () => import("@/views/salary_slip/Detail.vue"),
	},
]

export default routes
