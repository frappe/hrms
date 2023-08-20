import { createResource } from "frappe-ui"
import { employeeResource } from "./employee"

const transformLeaveData = (data) => {
	return data.map((leave) => {
		leave.doctype = "Leave Application"
		return leave
	})
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
