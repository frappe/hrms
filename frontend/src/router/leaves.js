const routes = [
	{
		name: "Leaves",
		path: "/leaves",
		component: () => import("@/views/leaves/Dashboard.vue"),
	},
	{
		name: "LeaveApplicationListView",
		path: "/leaves/list",
		component: () => import("@/views/leaves/List.vue"),
	},
	{
		name: "LeaveApplicationFormView",
		path: "/leaves/new",
		component: () => import("@/views/leaves/Form.vue"),
	},
	{
		name: "LeaveApplicationDetailView",
		path: "/leaves/:id",
		props: true,
		component: () => import("@/views/leaves/Details.vue"),
	}
]

export default routes