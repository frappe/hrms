const routes = [
	{
		name: "GrievanceListView",
		path: "/grievances",
		component: () => import("@/views/grievance/List.vue"),
	},
	{
		name: "GrievanceFormView",
		path: "/grievances/new",
		component: () => import("@/views/grievance/Form.vue"),
	},
	{
		name: "GrievanceDetailView",
		path: "/grievances/:id",
		props: true,
		component: () => import("@/views/grievance/Form.vue"),
	},
]

export default routes
