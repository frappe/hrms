import { createResource } from "frappe-ui"

export const unreadNotificationsCount = createResource({
	url: "hrms.api.get_unread_notifications_count",
	cache: "Unread Notifications Count",
	initialData: 0,
	auto: true,
})
