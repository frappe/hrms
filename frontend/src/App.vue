<template>
	<ion-app>
		<Menu />
		<ion-router-outlet id="main-content" />
		<Toasts />

		<!-- Install PWA dialog -->
		<Dialog
			:options="{
				title: 'Install Frappe HR',
				message:
					'Get the Frappe HR app on your home screen. It won\'t take up space on your phone!',
				icon: {
					name: 'download',
					appearance: 'primary',
				},
				size: 'xs',
				actions: [
					{
						label: 'Install',
						appearance: 'primary',
						handler: ({ close }) => {
							install()
							close() // closes dialog
						},
					},
				],
			}"
			v-model="showDialog"
		/>
	</ion-app>
</template>

<script setup>
import { IonApp, IonRouterOutlet } from "@ionic/vue"
import { ref } from "vue"

import { Toasts, Dialog } from "frappe-ui"

import Menu from "@/components/Menu.vue"

// Initialize deferredPrompt for use later to show browser install prompt.
const deferredPrompt = ref(null)
const showDialog = ref(false)

window.addEventListener("beforeinstallprompt", (e) => {
	// Prevent the mini-infobar from appearing on mobile
	e.preventDefault()
	// Stash the event so it can be triggered later.
	deferredPrompt.value = e
	showDialog.value = true
	// Optionally, send analytics event that PWA install promo was shown.
	console.log(`'beforeinstallprompt' event was fired.`)
})

window.addEventListener("appinstalled", () => {
	showDialog.value = false
	deferredPrompt.value = null
})

async function install() {
	deferredPrompt.value.prompt()
}
</script>
