const routes = [
	{
		name: "EmployeeAdvanceListView",
		path: "/employee-advance/list",
		component: () => import("@/views/employee_advance/List.vue"),
	},
	{
		name: "EmployeeAdvanceFormView",
		path: "/employee-advance/new",
		component: () => import("@/views/employee_advance/Form.vue"),
	},
	{
		name: "EmployeeAdvanceDetailView",
		path: "/employee-advance/:id",
		props: true,
		component: () => import("@/views/employee_advance/Form.vue"),
	},
]

export default routes
