import { createResource } from "frappe-ui"
import { employeeResource } from "./employee"

export const calendarEvents = createResource({
	url: "hrms.api.get_attendance_calendar_events",
	params: {
		employee: employeeResource.data.name,
		from_date: "2024-08-01",
		to_date: "2024-09-01",
	},
	auto: true,
	cache: "hrms:calendar_events",
	onSuccess: (data) => {
		console.log(data)
	},
})
