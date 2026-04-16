import { createResource } from "frappe-ui"

export const settings = createResource({
	url: "hrms.api.get_hr_settings",
	auto: true,
})