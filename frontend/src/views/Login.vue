<template>
	<ion-page>
		<ion-content class="ion-padding ">
			<div class="flex h-screen w-screen flex-col justify-center bg-white">
				<div class="text-3xl mb-5 font-medium text-gray-900 text-center">Welcome to FrappeHR</div>
				<div class="mx-auto mt-6 w-full px-8 sm:w-96">
					<form class="flex flex-col space-y-4" @submit.prevent="submit">
						<Input
							label="Email"
							placeholder="johndoe@mail.com"
							v-model="email"
							:type="email !== 'Administrator' ? 'email' : 'text'"
						/>
						<Input label="Password" type="password" placeholder="••••••" v-model="password" />
						<Button :loading="session.login.loading" appearance="primary"> Login </Button>
					</form>
				</div>
			</div>
		</ion-content>
	</ion-page>
</template>

<script setup>
import { IonPage, IonContent } from "@ionic/vue"
import { inject, ref } from "vue"
import { Input, Button } from "frappe-ui"

const email = ref(null)
const password = ref(null)

const session = inject("$session")
function submit(e) {
	session.login.submit({
		email: email.value,
		password: password.value,
	})
}
</script>
