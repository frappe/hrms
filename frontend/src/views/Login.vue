<template>
	<ion-page>
		<ion-content class="ion-padding">
			<div class="flex h-screen w-screen flex-col justify-center bg-white">
				<div class="flex flex-col mx-auto gap-3 items-center">
					<FrappeHRLogo class="h-8 w-8" />
					<div class="text-3xl font-semibold text-gray-900 text-center">
						Login to Frappe HR
					</div>
				</div>

				<div class="mx-auto mt-10 w-full px-8 sm:w-96">
					<form class="flex flex-col space-y-4" @submit.prevent="submit">
						<Input
							label="Email"
							placeholder="johndoe@mail.com"
							v-model="email"
							:type="email !== 'Administrator' ? 'email' : 'text'"
						/>
						<Input
							label="Password"
							type="password"
							placeholder="••••••"
							v-model="password"
						/>
						<ErrorMessage :message="errorMessage" />
						<Button
							:loading="session.login.loading"
							variant="solid"
							class="disabled:bg-gray-700 disabled:text-white !mt-6"
						>
							Login
						</Button>
					</form>
				</div>
			</div>

			<Dialog v-model="resetPassword">
				<template #body-title>
					<h2 class="text-lg font-bold">Reset Password</h2>
				</template>
				<template #body-content>
					<p>
						Your password has expired. Please reset your password to continue
					</p>
				</template>
				<template #actions>
					<a
						class="inline-flex items-center justify-center gap-2 transition-colors focus:outline-none text-white bg-gray-900 hover:bg-gray-800 active:bg-gray-700 focus-visible:ring focus-visible:ring-gray-400 h-7 text-base px-2 rounded"
						:href="resetPasswordLink"
						target="_blank"
					>
						Go to Reset Password page
					</a>
				</template>
			</Dialog>
		</ion-content>
	</ion-page>
</template>

<script setup>
import { IonPage, IonContent } from "@ionic/vue"
import { inject, ref } from "vue"
import { Input, Button, ErrorMessage, Dialog } from "frappe-ui"

import FrappeHRLogo from "@/components/icons/FrappeHRLogo.vue"

const email = ref(null)
const password = ref(null)
const errorMessage = ref("")
const resetPassword = ref(false)
const resetPasswordLink = ref("")

const session = inject("$session")

async function submit(e) {
	try {
		const response = await session.login(email.value, password.value)
		if (response.message === "Password Reset") {
			resetPassword.value = true
			resetPasswordLink.value = response.redirect_to
		} else {
			resetPassword.value = false
			resetPasswordLink.value = ""
		}
	} catch (error) {
		errorMessage.value = error.messages.join("\n")
	}
}
</script>
