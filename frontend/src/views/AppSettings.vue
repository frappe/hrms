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
							<h2 class="text-xl font-semibold text-gray-900">Settings</h2>
						</div>
					</header>

					<div class="flex flex-col gap-5 my-4 w-full p-4">
						<div class="flex flex-col bg-white rounded">
							<Switch
								size="md"
								label="Enable Push Notifications"
								:model-value="pushNotificationState"
								@update:model-value="togglePushNotifications"
							/>
						</div>
					</div>
				</div>
			</div>
		</ion-content>
	</ion-page>
</template>

<script setup>
import { IonPage, IonContent } from "@ionic/vue"
import { useRouter } from "vue-router"
import { FeatherIcon, Switch, toast } from "frappe-ui"

import { ref } from "vue"

const router = useRouter()
const pushNotificationState = ref(
	window.frappePushNotification.isNotificationEnabled()
)

const togglePushNotifications = (newValue) => {
	if (newValue) {
		enablePushNotifications()
	} else {
		window.frappePushNotification
			.disableNotification()
			.then((data) => {
				pushNotificationState.value = false // Disable the switch
				toast({
					title: "Success",
					text: "Push notifications disabled",
					icon: "check-circle",
					position: "bottom-center",
					iconClasses: "text-green-500",
				})
			})
			.catch((err) => {
				console.log(err)
				toast({
					title: "Error",
					text: "Something went wrong",
					icon: "error",
					position: "bottom-center",
					iconClasses: "text-red-500",
				})
			})
	}
}

const enablePushNotifications = () => {
	window.frappePushNotification
		.enableNotification()
		.then((data) => {
			console.log(data)
			let permission_granted = data.permission_granted
			let token = data.token
			if (permission_granted) {
				alert("Notification Activated")
				pushNotificationState.value = true
			} else {
				alert("Permission Denied ! Retry again later")
				pushNotificationState.value = false
			}
		})
		.catch((err) => {
			console.log(err)
			pushNotificationState.value = false
		})
}
</script>
