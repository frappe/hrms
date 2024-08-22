import { createResource } from "frappe-ui"
import { employeeResource } from "./employee"
import { ref } from "vue"

import dayjs from "@/utils/dayjs"

export const firstOfMonth = ref(dayjs().date(1).startOf("D"))

const getShiftDates = (shift) => {
	return shift.start_date == shift.end_date
		? dayjs(shift.start_date).format("D MMM")
		: `${dayjs(shift.start_date).format("D MMM")} - ${dayjs(shift.end_date).format("D MMM")}`
}

const getTotalShiftDays = (shift) => {
	if (!shift.end_date) return null
	const end_date = dayjs(shift.end_date)
	const start_date = dayjs(shift.start_date)
	return end_date.diff(start_date, "d")
}

export const calendarEvents = createResource({
	url: "hrms.api.get_attendance_calendar_events",
	auto: true,
	cache: "hrms:attendance_calendar_events",
	makeParams() {
		return {
			employee: employeeResource.data.name,
			from_date: firstOfMonth.value.format("YYYY-MM-DD"),
			to_date: firstOfMonth.value.endOf("M").format("YYYY-MM-DD"),
		}
	},
})

export const shifts = createResource({
	url: "hrms.api.get_shifts",
	auto: true,
	cache: "hrms:shifts",
	makeParams() {
		return {
			employee: employeeResource.data.name,
		}
	},
	transform: (data) => {
		return data.map((assignment) => {
			assignment.is_upcoming = !assignment.end_date || dayjs(assignment.end_date).isAfter(dayjs())
			assignment.start_time = assignment.start_time.split(":").slice(0, 2).join(":")
			assignment.end_time = assignment.end_time.split(":").splice(0, 2).join(":")
			assignment.dates = getShiftDates(assignment)
			assignment.total_shift_days = getTotalShiftDays(assignment)
			return assignment
		})
	},
})
