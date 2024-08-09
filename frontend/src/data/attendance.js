import { createResource } from "frappe-ui"
import { employeeResource } from "./employee"
import { ref } from "vue"

import dayjs from "@/utils/dayjs"

export const firstOfMonth = ref(dayjs().date(1).startOf("D"))

export const calendarEvents = createResource({
	url: "hrms.api.get_attendance_calendar_events",
	auto: true,
	makeParams() {
		return {
			employee: employeeResource.data.name,
			from_date: firstOfMonth.value.format("YYYY-MM-DD"),
			to_date: firstOfMonth.value.endOf("M").format("YYYY-MM-DD"),
		}
	},
})
