<template>
	<ion-page>
		<ion-content class="ion-padding">
			<div class="flex flex-col h-screen w-screen">
				<div class="w-full sm:w-96">
					<header
						class="flex flex-row bg-white shadow-sm py-4 px-3 items-center justify-between border-b sticky top-0 z-10"
					>
						<div class="flex flex-row items-center">
							<Button
								variant="ghost"
								class="!pl-0 hover:bg-white"
								@click="router.back()"
							>
								<FeatherIcon name="chevron-left" class="h-5 w-5" />
							</Button>
							<h2 class="text-xl font-semibold text-gray-900">{{ __("Settings") }} </h2>
						</div>
					</header>

					<div class="flex flex-col gap-5 my-4 w-full p-4">
						<div class="flex flex-col bg-white rounded">
							<div
								class="flex flex-row cursor-pointer flex-start p-4 items-center justify-between border-b"
								@click="openChangePasswordModal()"
							>
								<div class="flex flex-row items-center gap-3 grow">
									<FeatherIcon
										name="lock"
										class="h-5 w-5 text-gray-500"
									/>
									<div class="text-base font-normal text-gray-800">
										{{ __("Change Password") }}
									</div>
								</div>
								<FeatherIcon
									name="chevron-right"
									class="h-5 w-5 text-gray-500"
								/>
							</div>
						</div>

						<div class="flex flex-col bg-white rounded">
							<Switch
								size="md"
								:label="__('Enable Push Notifications')"
								:class="description ? 'p-2' : ''"
								:model-value="pushNotificationState"
								:disabled="disablePushSetting"
								:description="description"
								@update:model-value="togglePushNotifications"
							/>
						</div>

						<div
							v-if="isLoading"
							class="flex -mt-2 items-center justify-center gap-2"
						>
							<LoadingIndicator class="w-3 h-3 text-gray-800" />
							<span class="text-gray-900 text-sm">
								{{ pushNotificationState ? __("Disabling Push Notifications...") : __("Enabling Push Notifications...") }}
							</span>
						</div>
					</div>
				</div>
			</div>

			<ion-modal
				ref="modal"
				:is-open="isResetPasswordModalOpen"
				@didDismiss="closeChangePasswordModal"
				:initial-breakpoint="1"
				:breakpoints="[0, 1]"
			>
				<div class="w-full flex flex-col items-center justify-center gap-5 p-4 mb-5">
					<div class="flex flex-col gap-1.5 mt-2 items-center justify-center">
						<div class="font-bold text-xl">
							{{ __("Change Password") }}
						</div>
						<div class="font-medium text-gray-500 text-sm text-center">
							{{ __("Send password reset link to") }}
							<span class="font-semibold text-gray-900">{{ user.data.name }}</span>?
						</div>
					</div>

					<Button
						:loading="resetPasswordResource.loading"
						variant="solid"
						class="w-full py-5 text-sm disabled:bg-gray-700"
						@click="sendPasswordReset"
					>
						{{ __("Send Reset Link") }}
					</Button>
				</div>
			</ion-modal>
		</ion-content>
	</ion-page>
</template>

<script setup>
import { IonPage, IonContent, modalController } from "@ionic/vue"
import { useRouter } from "vue-router"
import { FeatherIcon, Switch, toast, LoadingIndicator, createResource, Input, ErrorMessage, Button } from "frappe-ui"

import { computed, inject, ref } from "vue"

import { arePushNotificationsEnabled } from "@/data/notifications"

const __ = inject("$translate")
const user = inject("$user")
const router = useRouter()

const resetPasswordError = ref("")
const isResetPasswordModalOpen = ref(false)
const pushNotificationState = ref(
	window.frappePushNotification?.isNotificationEnabled()
)
const isLoading = ref(false)

const disablePushSetting = computed(() => {
	return (
		!(
			window.frappe?.boot.push_relay_server_url &&
			arePushNotificationsEnabled.data
		) || isLoading.value
	)
})

const description = computed(() => {
	return !(
		window.frappe?.boot.push_relay_server_url &&
		arePushNotificationsEnabled.data
	)
		? __("Push notifications have been disabled on your site")
		: ""
})

const togglePushNotifications = (newValue) => {
	if (newValue) {
		enablePushNotifications()
	} else {
		isLoading.value = true
		window.frappePushNotification
			.disableNotification()
			.then(() => {
				pushNotificationState.value = false
				toast({
					title: __("Success"),
					text: __("Push notifications disabled"),
					icon: "check-circle",
					position: "bottom-center",
					iconClasses: "text-green-500",
				})
			})
			.catch((error) => {
				toast({
					title: __("Error"),
					text: __(error.message),
					icon: "alert-circle",
					position: "bottom-center",
					iconClasses: "text-red-500",
				})
			})
			.finally(() => {
				isLoading.value = false
			})
	}
}
const openChangePasswordModal = async () => {
	isResetPasswordModalOpen.value = true
	console.log("Opening change password modal")
}

const closeChangePasswordModal = async () => {
	isResetPasswordModalOpen.value = false
}
const enablePushNotifications = () => {
	isLoading.value = true

	window.frappePushNotification
		.enableNotification()
		.then((data) => {
			if (data.permission_granted) {
				pushNotificationState.value = true
			} else {
				toast({
					title: __("Error"),
					text: __("Push Notification permission denied"),
					icon: "alert-circle",
					position: "bottom-center",
					iconClasses: "text-red-500",
				})
				pushNotificationState.value = false
			}
		})
		.catch((error) => {
			toast({
				title: __("Error"),
				text: __(error.message),
				icon: "alert-circle",
				position: "bottom-center",
				iconClasses: "text-red-500",
			})
			pushNotificationState.value = false
		})
		.finally(() => {
			isLoading.value = false
		})
}

const resetPasswordResource = createResource({
	url: "frappe.core.doctype.user.user.reset_password",
	method: "POST",
	onSuccess() {
		modalController.dismiss()
		toast({
			title: __("Success"),
			text: __("Password reset link has been sent to your email."),
			icon: "check-circle",
			position: "bottom-center",
			iconClasses: "text-green-500",
		})
	},
	onError(error) {
		toast({
			title: __("Error"),
			text: error.messages?.[0] || __("Failed to send reset link"),
			icon: "alert-circle",
			position: "bottom-center",
			iconClasses: "text-red-500",
		})
	},
})

function sendPasswordReset() {
	resetPasswordResource.submit({ user: user.data.name })
}

</script>