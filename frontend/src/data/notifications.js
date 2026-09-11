import { createResource, createListResource } from "frappe-ui"
import { userResource } from "./user"

export const unreadNotificationsCount = createResource({
	url: "hrms.api.get_unread_notifications_count",
	cache: "hrms:unread_notifications_count",
	initialData: 0,
	auto: true,
})

export const notifications = createListResource({
	doctype: "PWA Notification",
	filters: { to_user: userResource.data.name, read: 0 },
	fields: [
		"name",
		"from_user",
		"message",
		"read",
		"creation",
		"reference_document_type",
		"reference_document_name",
	],
	auto: false,
	pageLength: 10,
	cache: "hrms:notifications",
	orderBy: "creation desc",
	onSuccess() {
		unreadNotificationsCount.reload()
	},
})

export const arePushNotificationsEnabled = createResource({
	url: "hrms.api.are_push_notifications_enabled",
	cache: "hrms:push_notifications_enabled",
	auto: true,
})
