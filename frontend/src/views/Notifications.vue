<template>
	<BaseLayout pageTitle="Notifications">
		<template #body>
			<div class="flex flex-col gap-4 mt-5 p-4">
				<div
					v-if="unreadNotificationsCount.data"
					class="flex flex-row justify-between items-center"
				>
					<div class="text-lg text-gray-800 font-semibold">
						{{ unreadNotificationsCount.data }} Unread
					</div>
					<Button
						appearance="white"
						icon-left="check-circle"
						class="ml-auto"
						@click="markAllAsRead.submit"
						:loading="markAllAsRead.loading"
					>
						Mark all as read
					</Button>
				</div>

				<div class="flex flex-col bg-white rounded-lg">
					<router-link
						:class="[
							'flex flex-row items-start p-4 justify-between border-b before:mt-4',
							`before:content-[''] before:mr-2 before:shrink-0 before:w-1.5 before:h-1.5 before:rounded-full`,
							item.read ? 'bg-white-500' : 'before:bg-blue-500',
						]"
						v-for="item in notifications.data"
						:key="item.name"
						:to="getItemRoute(item)"
						@click="markAsRead(item.name)"
					>
						<EmployeeAvatar :userID="item.from_user" size="md" class="mt-0.5" />
						<div class="flex flex-col gap-0.5 grow ml-3">
							<div
								class="text-base font-normal text-gray-800"
								v-html="item.message"
							></div>
							<div class="text-sm font-normal text-gray-500">
								{{ dayjs(item.creation).fromNow() }}
							</div>
						</div>
					</router-link>
				</div>
			</div>
		</template>
	</BaseLayout>
</template>

<script setup>
import BaseLayout from "@/components/BaseLayout.vue"
import { createListResource, createResource } from "frappe-ui"

import { inject, onMounted } from "vue"
import EmployeeAvatar from "@/components/EmployeeAvatar.vue"

import { unreadNotificationsCount } from "@/data/notifications"

const user = inject("$user")
const dayjs = inject("$dayjs")
const socket = inject("$socket")

const notifications = createListResource({
	doctype: "PWA Notification",
	filters: { to_user: user.data.name },
	fields: [
		"name",
		"from_user",
		"message",
		"read",
		"creation",
		"reference_document_type",
		"reference_document_name",
	],
	auto: true,
	orderBy: "creation desc",
})

const markAllAsRead = createResource({
	url: "hrms.api.mark_all_notifications_as_read",
	onSuccess() {
		notifications.reload()
		unreadNotificationsCount.reload()
	},
})

function markAsRead(name) {
	notifications.setValue.submit(
		{ name, read: 1 },
		{
			onSuccess: () => {
				unreadNotificationsCount.reload()
			},
		}
	)
}

function getItemRoute(item) {
	return {
		name: `${item.reference_document_type.replace(/\s+/g, "")}DetailView`,
		params: { id: item.reference_document_name },
	}
}

socket.on("hrms:update_notifications", () => {
	notifications.reload()
})

onMounted(async () => {
	await user.promise
})
</script>
