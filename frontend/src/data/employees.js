import { createResource } from "frappe-ui"
import { reactive } from "vue"
import { employeeResource } from "./employee"

let employeesByID = reactive({})

export const employees = createResource({
	url: "hrms.api.get_employees",
	cache: "Employees",
	initialData: [],
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

export function employeeInfo(empID) {
	if (!empID)
		empID = employeeResource.data.name

	return employeesByID[empID]
}

