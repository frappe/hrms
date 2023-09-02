<template>
	<ion-page>
		<ion-content class="ion-padding">
			<div class="flex flex-col h-screen w-screen">
				<div class="w-full sm:w-96">
					<header
						class="flex flex-row bg-white shadow-sm py-4 px-2 items-center justify-between border-b sticky top-0 z-10"
					>
						<div class="flex flex-row gap-1">
							<Button
								variant="ghost"
								class="!px-0 !py-0"
								@click="router.back()"
							>
								<FeatherIcon name="chevron-left" class="h-5 w-5" />
							</Button>
							<h2 class="text-2xl font-semibold text-gray-900">
								Notifications
							</h2>
						</div>
					</header>

					<div class="flex flex-col gap-4 mt-5 p-4">
						<div
							v-if="unreadNotificationsCount.data"
							class="flex flex-row justify-between items-center"
						>
							<div class="text-lg text-gray-800 font-semibold">
								{{ unreadNotificationsCount.data }} Unread
							</div>
							<Button
								variant="outline"
								icon-left="check-circle"
								class="ml-auto"
								@click="markAllAsRead.submit"
								:loading="markAllAsRead.loading"
							>
								Mark all as read
							</Button>
						</div>

						<div
							class="flex flex-col bg-white rounded-lg"
							v-if="notifications.data?.length"
						>
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
								<EmployeeAvatar :userID="item.from_user" size="md" />
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

						<EmptyState v-else message="You have no notifications" />
					</div>
				</div>
			</div>
		</ion-content>
	</ion-page>
</template>

<script setup>
import { IonContent, IonPage } from "@ionic/vue"
import { useRouter } from "vue-router"
import { createListResource, createResource, FeatherIcon } from "frappe-ui"

import { inject, onBeforeUnmount, onMounted } from "vue"
import EmployeeAvatar from "@/components/EmployeeAvatar.vue"

import { unreadNotificationsCount } from "@/data/notifications"
import EmptyState from "@/components/EmptyState.vue"

const user = inject("$user")
const dayjs = inject("$dayjs")
const socket = inject("$socket")
const router = useRouter()

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

onMounted(() => {
	socket.off("hrms:update_notifications")
	socket.on("hrms:update_notifications", () => {
		notifications.reload()
	})
})

onBeforeUnmount(() => {
	socket.off("hrms:update_notifications")
})
</script>
