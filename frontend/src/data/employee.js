import { createResource } from "frappe-ui"

import { redirectToAmeideOidc } from "@/utils/auth"

export const employeeResource = createResource({
	url: "hrms.api.get_current_employee_info",
	cache: "hrms:employee",
	onError(error) {
		if (error && error.exc_type === "AuthenticationError") {
			redirectToAmeideOidc()
		}
	},
})
