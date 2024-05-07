const routes = [
	{
		name: "LeaveApplicationListView",
		path: "/leave-applications",
		component: () => import("@/views/leave/List.vue"),
	},
	{
		name: "LeaveApplicationFormView",
		path: "/leave-applications/new",
		component: () => import("@/views/leave/Form.vue"),
	},
	{
		name: "LeaveApplicationDetailView",
		path: "/leave-applications/:id",
		props: true,
		component: () => import("@/views/leave/Form.vue"),
	},
]

export default routes
