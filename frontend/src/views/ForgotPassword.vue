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
							@click="goBack"
						>
							<FeatherIcon name="chevron-left" class="h-5 w-5" />
						</Button>
						<h2 class="text-xl font-semibold text-gray-900">{{ __("Reset Password") }}</h2>
					</header>

					<div class="bg-white grow overflow-y-auto">
						<form class="flex flex-col space-y-4 p-4" @submit.prevent="sendPasswordReset">
							<p class="text-sm leading-5 text-gray-600">
								{{ __("Enter your email address and we'll send you a link to reset your password.") }}
							</p>
							<Input
								:label="__('Email') + ' *'"
								type="email"
								placeholder="johndoe@mail.com"
								v-model="email"
								autocomplete="username"
								required
							/>
						</form>
					</div>

					<div
						class="px-4 pt-4 pb-4 standalone:pb-safe-bottom sm:w-96 bg-white sticky bottom-0 w-full drop-shadow-xl z-40 border-t rounded-t-lg"
					>
						<ErrorMessage class="mb-2" :message="errorMessage" />
						<Button
							class="w-full rounded py-5 text-base disabled:bg-gray-700 disabled:text-white"
							:loading="forgotPasswordResource.loading"
							variant="solid"
							@click="sendPasswordReset"
						>
							{{ __("Send Reset Link") }}
						</Button>
					</div>
				</div>
			</div>
		</ion-content>
	</ion-page>
</template>

<script setup>
import { IonPage, IonContent } from "@ionic/vue"
import { useRoute, useRouter } from "vue-router"
import { FeatherIcon, toast, createResource, Input, ErrorMessage, Button } from "frappe-ui"

import { inject, ref } from "vue"

const __ = inject("$translate")
const route = useRoute()
const router = useRouter()

const email = ref(Array.isArray(route.query.email) ? route.query.email[0] : route.query.email || "")
const errorMessage = ref("")

const forgotPasswordResource = createResource({
	url: "frappe.core.doctype.user.user.reset_password",
	method: "POST",
	onSuccess() {
		toast({
			title: __("Success"),
			text: __("Password reset link has been sent to your email."),
			icon: "check-circle",
			position: "bottom-center",
			iconClasses: "text-green-500",
		})
		errorMessage.value = ""
		router.replace({ name: "Login" })
	},
	onError(error) {
		errorMessage.value = error.messages?.[0] || __("Failed to send reset link")
	},
})

function isValidEmail(value) {
	return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)
}

function goBack() {
	if (window.history.state?.back) {
		router.back()
		return
	}

	router.replace({ name: "Login" })
}

function sendPasswordReset() {
	const emailValue = (email.value || "").trim()

	if (!emailValue) {
		errorMessage.value = __("Please enter your email address")
		return
	}

	if (!isValidEmail(emailValue)) {
		errorMessage.value = __("Please enter a valid email address")
		return
	}

	errorMessage.value = ""
	forgotPasswordResource.submit({ user: emailValue })
}
</script>
