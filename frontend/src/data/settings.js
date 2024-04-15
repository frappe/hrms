import { createResource } from "frappe-ui"

export const allowCheckinFromMobile = createResource({
	url: "hrms.api.is_employee_checkin_allowed",
	auto: true,
})
