const routes = [
	{
		name: "EmployeeAdvanceListView",
		path: "/employee-advances",
		component: () => import("@/views/employee_advance/List.vue"),
	},
	{
		name: "EmployeeAdvanceFormView",
		path: "/employee-advances/new",
		component: () => import("@/views/employee_advance/Form.vue"),
	},
	{
		name: "EmployeeAdvanceDetailView",
		path: "/employee-advances/:id",
		props: true,
		component: () => import("@/views/employee_advance/Form.vue"),
	},
]

export default routes
