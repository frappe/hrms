import { createListResource } from "frappe-ui"
import { reactive } from "vue"
import { employeeResource } from "./employee"

let employeesByID = reactive({})

export const employees = createListResource({
	doctype: "Employee",
	fields: [
		"name",
		"employee_name",
		"designation",
		"department",
		"company",
		"reports_to",
		"user_id",
		"image",
		"status",
	],
	auto: true,
	transform(data) {
		return data.map((employee) => {
			employee.isActive = employee.status === "Active"
			employeesByID[employee.name] = employee
			return employee
		})
	},
	onError(error) {
		if (error && error.exc_type === "AuthenticationError") {
			router.push({ name: "Login" })
		}
	},
})

export function getEmployeeInfo(employeeID) {
	if (!employeeID) employeeID = employeeResource.data.name

	return employeesByID[employeeID]
}
