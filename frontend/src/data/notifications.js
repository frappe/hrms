import { createResource } from "frappe-ui"
import socket from "../socket"

export const unreadNotificationsCount = createResource({
	url: "hrms.api.get_unread_notifications_count",
	cache: "Unread Notifications Count",
	initialData: 0,
	auto: true,
})

socket.on("hrms:update_notifications", () => {
	unreadNotificationsCount.reload()
})
