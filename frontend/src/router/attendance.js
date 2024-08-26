const routes = [
	{
		name: "ShiftRequestListView",
		path: "/shift-requests",
		component: () => import("@/views/attendance/ShiftRequestList.vue"),
	},
	{
		name: "ShiftRequestFormView",
		path: "/shift-requests/new",
		component: () => import("@/views/attendance/ShiftRequestForm.vue"),
	},
	{
		name: "ShiftRequestDetailView",
		path: "/shift-requests/:id",
		props: true,
		component: () => import("@/views/attendance/ShiftRequestForm.vue"),
	},
]

export default routes
