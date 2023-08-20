import { createResource } from "frappe-ui"
import { employeeResource } from "./employee"

import dayjs from "@/utils/dayjs"

const transformLeaveData = (data) => {
	return data.map((leave) => {
		leave.leave_dates = get_leave_dates(leave)
		leave.doctype = "Leave Application"
		return leave
	})
}

const get_leave_dates = (leave) => {
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
		employee: employeeResource.data.name,
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
		employee: employeeResource.data.name,
		user_id: employeeResource.data.user_id,
		limit: 5,
	},
	auto: true,
	transform(data) {
		return transformLeaveData(data)
	},
})
