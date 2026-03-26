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
						<!-- Push Notifications -->
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
						<!-- Loading Indicator -->
						<div
							v-if="isLoading"
							class="flex -mt-2 items-center justify-center gap-2"
						>
							<LoadingIndicator class="w-3 h-3 text-gray-800" />
							<span class="text-gray-900 text-sm">
								{{ pushNotificationState ? __("Disabling Push Notifications...") : __("Enabling Push Notifications...") }}
							</span>
						</div>

						<!-- HortiHub Settings (HR Manager / System Manager only) -->
						<template v-if="isHRManager">
							<div class="text-sm font-semibold text-gray-700 mt-2">
								{{ __("HortiHub Settings") }}
							</div>
							<div class="flex flex-col bg-white rounded divide-y">
								<Switch
									size="md"
									:label="__('Require Photo on Check-in')"
									:description="__('Employees must take a photo when checking in or out')"
									class="p-2"
									:model-value="hrSettings.require_checkin_photo"
									:disabled="savingSettings"
									@update:model-value="(val) => updateHRSetting('require_checkin_photo', val)"
								/>
								<Switch
									size="md"
									:label="__('Hide Accounting Features')"
									:description="__('Hide expense claims and advances from the mobile app')"
									class="p-2"
									:model-value="hrSettings.hide_accounting_features"
									:disabled="savingSettings"
									@update:model-value="(val) => updateHRSetting('hide_accounting_features', val)"
								/>
							</div>
							<div
								v-if="savingSettings"
								class="flex -mt-2 items-center justify-center gap-2"
							>
								<LoadingIndicator class="w-3 h-3 text-gray-800" />
								<span class="text-gray-900 text-sm">{{ __("Saving...") }}</span>
							</div>
						</template>

						<!-- Read-only summary for regular employees -->
						<template v-else-if="hrSettingsLoaded">
							<div class="text-sm font-semibold text-gray-700 mt-2">
								{{ __("App Configuration") }}
							</div>
							<div class="flex flex-col bg-white rounded p-3 gap-2 text-sm text-gray-600">
								<div class="flex items-center gap-2">
									<FeatherIcon
										:name="hrSettings.require_checkin_photo ? 'check-circle' : 'circle'"
										class="h-4 w-4"
										:class="hrSettings.require_checkin_photo ? 'text-green-500' : 'text-gray-400'"
									/>
									<span>{{ __("Photo required on check-in") }}</span>
								</div>
								<div class="flex items-center gap-2">
									<FeatherIcon
										:name="hrSettings.hide_accounting_features ? 'check-circle' : 'circle'"
										class="h-4 w-4"
										:class="hrSettings.hide_accounting_features ? 'text-green-500' : 'text-gray-400'"
									/>
									<span>{{ __("Accounting features hidden") }}</span>
								</div>
							</div>
						</template>
					</div>
				</div>
			</div>
		</ion-content>
	</ion-page>
</template>

<script setup>
import { IonPage, IonContent } from "@ionic/vue"
import { useRouter } from "vue-router"
import { FeatherIcon, Switch, toast, LoadingIndicator, createResource, frappeRequest } from "frappe-ui"

import { computed, inject, ref, reactive, onMounted } from "vue"

import { arePushNotificationsEnabled } from "@/data/notifications"

const __ = inject("$translate")
const user = inject("$user")
const router = useRouter()
const pushNotificationState = ref(
	window.frappePushNotification?.isNotificationEnabled()
)
const isLoading = ref(false)
const savingSettings = ref(false)
const hrSettingsLoaded = ref(false)

const hrSettings = reactive({
	require_checkin_photo: false,
	hide_accounting_features: true,
})

const isHRManager = computed(() => {
	const roles = user?.data?.roles || []
	return roles.includes("HR Manager") || roles.includes("System Manager")
})

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

onMounted(async () => {
	try {
		const data = await frappeRequest({ url: "hrms.api.get_hr_settings" })
		hrSettings.require_checkin_photo = !!data.require_checkin_photo
		hrSettings.hide_accounting_features = !!data.hide_accounting_features
		hrSettingsLoaded.value = true
	} catch (err) {
		console.error("Failed to load HR settings", err)
	}
})

async function updateHRSetting(fieldname, value) {
	savingSettings.value = true
	hrSettings[fieldname] = value
	try {
		await frappeRequest({
			url: "hrms.api.update_horthub_settings",
			method: "POST",
			params: { fieldname, value: value ? 1 : 0 },
		})
		toast({
			title: __("Saved"),
			text: __("Setting updated"),
			icon: "check-circle",
			position: "bottom-center",
			iconClasses: "text-green-500",
		})
	} catch (err) {
		hrSettings[fieldname] = !value
		toast({
			title: __("Error"),
			text: __("Failed to save setting"),
			icon: "alert-circle",
			position: "bottom-center",
			iconClasses: "text-red-500",
		})
	} finally {
		savingSettings.value = false
	}
}

const togglePushNotifications = (newValue) => {
	if (newValue) {
		enablePushNotifications()
	} else {
		isLoading.value = true
		window.frappePushNotification
			.disableNotification()
			.then((data) => {
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
</script>
