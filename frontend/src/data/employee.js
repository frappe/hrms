import router from "@/router"
import { createResource } from "frappe-ui"

export const employeeResource = createResource({
	url: "hr_app.api.get_current_employee_info",
	cache: "hrms:employee",
	onError(error) {
		if (error && error.exc_type === "AuthenticationError") {
			router.push("/login")
		}
	},
})
