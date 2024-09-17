import { createListResource } from "frappe-ui"
import { employeeResource } from "./employee"

import dayjs from "@/utils/dayjs"

export const getDates = (shift) => {
	const fromDate = dayjs(shift.from_date).format("D MMM")
	const toDate = shift.to_date ? dayjs(shift.to_date).format("D MMM") : "Ongoing"
	return fromDate == toDate ? fromDate : `${fromDate} - ${toDate}`
}

export const getTotalDays = (shift) => {
	if (!shift.to_date) return null
	const toDate = dayjs(shift.to_date)
	const fromDate = dayjs(shift.from_date)
	return toDate.diff(fromDate, "d") + 1
}

export const getShiftDates = (shift) => {
	const startDate = dayjs(shift.start_date).format("D MMM")
	const endDate = shift.end_date ? dayjs(shift.end_date).format("D MMM") : "Ongoing"
	return startDate == endDate ? startDate : `${startDate} - ${endDate}`
}

export const getTotalShiftDays = (shift) => {
	if (!shift.end_date) return null
	const end_date = dayjs(shift.end_date)
	const start_date = dayjs(shift.start_date)
	return end_date.diff(start_date, "d") + 1
}

export const getShiftTiming = (shift) => {
	return (
		shift.start_time.split(":").slice(0, 2).join(":") +
		" - " +
		shift.end_time.split(":").splice(0, 2).join(":")
	)
}

export const myAttendanceRequests = createListResource({
	doctype: "Attendance Request",
	fields: [
		"name",
		"reason",
		"from_date",
		"to_date",
		"include_holidays",
		"shift",
		"docstatus",
		"creation",
	],
	filters: {
		employee: employeeResource.data?.name,
		docstatus: ["!=", 2],
	},
	orderBy: "modified desc",
	auto: true,
	cache: "hrms:attendance_requests",
	transform: (data) => {
		return data.map((request) => {
			request.doctype = "Attendance Request"
			request.attendance_dates = getDates(request)
			request.total_attendance_days = getTotalDays(request)
			return request
		})
	},
})

export const myShiftRequests = createListResource({
	doctype: "Shift Request",
	fields: ["name", "shift_type", "from_date", "to_date", "status", "docstatus", "creation"],
	filters: {
		employee: employeeResource.data?.name,
		docstatus: ["!=", 2],
	},
	orderBy: "modified desc",
	auto: true,
	cache: "hrms:shift_requests",
	transform: (data) => {
		return data.map((request) => {
			request.doctype = "Shift Request"
			request.shift_dates = getDates(request)
			request.total_shift_days = getTotalDays(request)
			return request
		})
	},
})
