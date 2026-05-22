<template>
	<ion-page>
		<ion-content>
			<div class="flex h-screen w-screen flex-col items-center justify-center bg-gray-100 px-6">
				<div class="flex flex-col items-center gap-4">
					<div class="flex h-10 w-10 items-center justify-center rounded-xl bg-gray-500 text-white">
						<FeatherIcon name="box" class="h-5 w-5" />
					</div>
					<h1 class="text-xl font-semibold text-gray-900">
						{{ __("Forgot Password") }}
					</h1>
				</div>

				<div class="mt-6 w-full max-w-sm rounded-lg border border-gray-200 bg-white px-10 py-11">
					<form class="flex flex-col gap-5" @submit.prevent="resetPassword">
						<Input
							v-model="email"
							type="email"
							:placeholder="__('Email Address')"
							autocomplete="email"
						>
							<template #prefix>
								<FeatherIcon name="mail" class="h-4 w-4 text-gray-500" />
							</template>
						</Input>

						<ErrorMessage :message="errorMessage" />

						<Button
							:loading="isSubmitting"
							variant="solid"
							class="h-7 bg-gray-900 text-base text-white hover:bg-gray-800 active:bg-gray-700 disabled:bg-gray-700 disabled:text-white"
						>
							{{ __("Reset Password") }}
						</Button>
					</form>

					<div
						v-if="successMessage"
						class="mt-4 text-center text-sm font-medium text-green-700"
					>
						{{ successMessage }}
					</div>

					<router-link
						class="mt-5 block text-center text-sm font-medium text-gray-900 hover:text-gray-700"
						:to="{ name: 'Login' }"
					>
						{{ __("Back to Login") }}
					</router-link>
				</div>
			</div>
		</ion-content>
	</ion-page>
</template>

<script setup>
import { IonContent, IonPage } from "@ionic/vue"
import { inject, ref } from "vue"
import { Button, ErrorMessage, FeatherIcon, Input, call, toast } from "frappe-ui"

const __ = inject("$translate")

const email = ref("")
const errorMessage = ref("")
const successMessage = ref("")
const isSubmitting = ref(false)

async function resetPassword() {
	errorMessage.value = ""
	successMessage.value = ""

	if (!email.value) {
		errorMessage.value = __("Please enter your email address")
		return
	}

	isSubmitting.value = true
	try {
		await call("frappe.core.doctype.user.user.reset_password", {
			user: email.value,
		})

		successMessage.value = __("If this email is registered with us, we have sent password reset instructions to it. Please check your inbox.")
		toast({
			title: __("Success"),
			text: successMessage.value,
			icon: "check-circle",
			position: "bottom-center",
			iconClasses: "text-green-500",
		})
	} catch (error) {
		errorMessage.value = error.messages?.join("\n") || error.message || __("Unable to reset password")
	} finally {
		isSubmitting.value = false
	}
}
</script>
