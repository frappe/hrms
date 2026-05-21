const routes = [
	{
		name: "TimesheetListView",
		path: "/timesheets",
		component: () => import("@/views/timesheet/List.vue"),
	},
	{
		name: "TimesheetTimer",
		path: "/timesheets/timer",
		component: () => import("@/views/timesheet/Timer.vue"),
	},
	{
		name: "TimesheetFormView",
		path: "/timesheets/new",
		component: () => import("@/views/timesheet/Form.vue"),
	},
	{
		name: "TimesheetDetailView",
		path: "/timesheets/:id",
		props: true,
		component: () => import("@/views/timesheet/Form.vue"),
	},
]
export default routes
