const routes = [
	{
		name: "CompensatoryLeaveRequestListView",
		path: "/compensatory-leave-requests",
		component: () => import("@/views/leave/CompensatoryLeaveRequestList.vue"),
	},
	{
		name: "CompensatoryLeaveRequestFormView",
		path: "/compensatory-leave-requests/new",
		component: () => import("@/views/leave/CompensatoryLeaveRequestForm.vue"),
	},
	{
		name: "CompensatoryLeaveRequestDetailView",
		path: "/compensatory-leave-requests/:id",
		props: true,
		component: () => import("@/views/leave/CompensatoryLeaveRequestForm.vue"),
	},
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
