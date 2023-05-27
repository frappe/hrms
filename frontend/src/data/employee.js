import { createResource } from "frappe-ui"

export const employeeResource = createResource({
	url: "hrms.api.get_current_employee_info",
	cache: "Employee",
})