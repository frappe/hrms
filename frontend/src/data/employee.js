import { createResource } from "frappe-ui"

export const employee = createResource({
	url: "hrms.api.get_employee_info",
	cache: "Employee"
})