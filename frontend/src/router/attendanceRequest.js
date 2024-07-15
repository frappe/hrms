const routes = [
	{
		name: "AttendanceRequestListView",
		path: "/attendance-request",
		component: () => import("@/views/attendance_request/List.vue"),
	},
	{
		name: "AttendanceRequestFormView",
		path: "/attendance-request/new",
		component: () => import("@/views/attendance_request/Form.vue"),
	},
	{
		name: "AttendanceRequestDetailView",
		path: "/attendance-request/:id",
		props: true,
		component: () => import("@/views/attendance_request/Form.vue"),
	},
]

export default routes


