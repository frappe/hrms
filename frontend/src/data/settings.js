import { createResource } from "frappe-ui"

export const allowCheckinForMobile = createResource({
	url: "hrms.api.is_employee_checkin_allowed",
	auto: true,
})
