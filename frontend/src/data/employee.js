import { createResource } from "frappe-ui"

export const employeeResource = createResource({
	url: "hrms.api.get_employee_info",
	cache: "Employee",
})