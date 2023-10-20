const routes = [
	{
		name: "LeaveApplicationListView",
		path: "/leave/list",
		component: () => import("@/views/leave/List.vue"),
	},
	{
		name: "LeaveApplicationFormView",
		path: "/leave/new",
		component: () => import("@/views/leave/Form.vue"),
	},
	{
		name: "LeaveApplicationDetailView",
		path: "/leave/:id",
		props: true,
		component: () => import("@/views/leave/Form.vue"),
	},
]

export default routes
