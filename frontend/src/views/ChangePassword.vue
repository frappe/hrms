<template>
	<ion-page>
		<ion-content :fullscreen="true">
			<div class="flex flex-col h-full w-full">
				<div class="w-full h-full bg-white sm:w-96 flex flex-col">
					<header
						class="flex flex-row bg-white shadow-sm py-4 px-3 items-center sticky top-0 z-[1000]"
					>
						<Button
							variant="ghost"
							class="!pl-0 hover:bg-white"
							@click="router.back()"
						>
							<FeatherIcon name="chevron-left" class="h-5 w-5" />
						</Button>
						<h2 class="text-xl font-semibold text-gray-900">{{ __("Change Password") }}</h2>
					</header>

					<div class="bg-white grow overflow-y-auto">
						<form class="flex flex-col space-y-4 p-4" @submit.prevent="submitPasswordChange">
							<Input
								:label="__('Current Password') + ' *'"
								type="password"
								v-model="currentPassword"
								autocomplete="current-password"
								required
							/>
							<Input
								:label="__('New Password') + ' *'"
								type="password"
								v-model="newPassword"
								autocomplete="new-password"
								required
							/>
							<Input
								:label="__('Confirm New Password') + ' *'"
								type="password"
								v-model="confirmPassword"
								autocomplete="new-password"
								required
							/>
						</form>
					</div>

					<div
						class="px-4 pt-4 pb-4 standalone:pb-safe-bottom sm:w-96 bg-white sticky bottom-0 w-full drop-shadow-xl z-40 border-t rounded-t-lg"
					>
						<ErrorMessage class="mb-2" :message="changePasswordError" />
						<Button
							class="w-full rounded py-5 text-base disabled:bg-gray-700 disabled:text-white"
							:loading="updatePasswordResource.loading"
							variant="solid"
							@click="submitPasswordChange"
						>
							{{ __("Update Password") }}
						</Button>
					</div>
				</div>
			</div>
		</ion-content>
	</ion-page>
</template>

<script setup>
import { IonPage, IonContent } from "@ionic/vue"
import { useRouter } from "vue-router"
import { FeatherIcon, toast, createResource, Input, ErrorMessage, Button } from "frappe-ui"

import { inject, ref } from "vue"

const __ = inject("$translate")
const router = useRouter()

const changePasswordError = ref("")
const currentPassword = ref("")
const newPassword = ref("")
const confirmPassword = ref("")

const updatePasswordResource = createResource({
	url: "frappe.core.doctype.user.user.update_password",
	method: "POST",
	onSuccess() {
		toast({
			title: __("Success"),
			text: __("Your password has been updated."),
			icon: "check-circle",
			position: "bottom-center",
			iconClasses: "text-green-500",
		})
		resetForm()
		router.back()
	},
	onError(error) {
		changePasswordError.value = error.messages?.[0] || __("Failed to update password")
	},
})

function resetForm() {
	changePasswordError.value = ""
	currentPassword.value = ""
	newPassword.value = ""
	confirmPassword.value = ""
}

function submitPasswordChange() {
	if (!currentPassword.value || !newPassword.value || !confirmPassword.value) {
		changePasswordError.value = __("Please fill all fields")
		return
	}

	if (newPassword.value !== confirmPassword.value) {
		changePasswordError.value = __("New passwords do not match")
		return
	}

	changePasswordError.value = ""
	updatePasswordResource.submit({
		old_password: currentPassword.value,
		new_password: newPassword.value,
	})
}
</script>
