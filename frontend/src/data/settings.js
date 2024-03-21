import { createResource } from "frappe-ui"

export const DisableCheckinForMobileSetting = createResource({
		url: "hrms.api.get_disable_checkin_for_mobile_setting",
		auto: true
	})
