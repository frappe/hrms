import { createResource } from "frappe-ui"
import { getEmployee } from "./employee"

import dayjs from "@/utils/dayjs"

const employee = getEmployee()

const transformLeaveData = (data) => {
	return data.map((leave) => {
		leave.leave_dates = getLeaveDates(leave)
		leave.doctype = "Leave Application"
		return leave
	})
}

export const getLeaveDates = (leave) => {
	if (leave.from_date == leave.to_date)
		return dayjs(leave.from_date).format("D MMM")
	else
		return `${dayjs(leave.from_date).format("D MMM")} - ${dayjs(
			leave.to_date
		).format("D MMM")}`
}

export const myLeaves = createResource({
	url: "hrms.api.get_employee_leave_applications",
	params: {
		employee: employee.name,
		limit: 5,
	},
	auto: true,
	transform(data) {
		return transformLeaveData(data)
	},
})

export const teamLeaves = createResource({
	url: "hrms.api.get_team_leave_applications",
	params: {
		employee: employee.name,
		user_id: employee.user_id,
		limit: 5,
	},
	auto: true,
	transform(data) {
		return transformLeaveData(data)
	},
})
