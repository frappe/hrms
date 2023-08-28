<template>
	<!-- Install PWA dialog -->
	<Dialog
		:options="{
			title: 'Install Frappe HR',
			message:
				'Get the Frappe HR app on your home screen. It won\'t take up any space on your phone!',
			size: 'xs',
			actions: [
				{
					label: 'Install',
					appearance: 'primary',
					'icon-left': 'download',
					handler: ({ close }) => {
						install()
						close() // closes dialog
					},
				},
			],
		}"
		v-model="showDialog"
	/>

	<!-- iOS installation info message -->
	<Popover :show="iosInstallMessage" placement="bottom">
		<template #body>
			<div
				class="mt-[90vh] mx-2 text-center rounded-xl bg-blue-100 px-3 py-5 text-xs text-blue-700 shadow-xl"
			>
				<span class="inline-flex items-center whitespace-nowrap">
					<span>Install Frappe HR on your iPhone: tap&nbsp;</span>
					<FeatherIcon name="share" class="h-4 w-4 text-gray-700" />
					<span>&nbsp;and then Add to Home Screen</span>
				</span>
			</div>
		</template>
	</Popover>
</template>

<script setup>
import { ref } from "vue"

import { Dialog, Popover, FeatherIcon } from "frappe-ui"

// Initialize deferredPrompt for use later to show browser install prompt.
const deferredPrompt = ref(null)
const showDialog = ref(false)
const iosInstallMessage = ref(false)

const isIos = () => {
	// Detects if device is on iOS
	const userAgent = window.navigator.userAgent.toLowerCase()
	return /iphone|ipad|ipod/.test(userAgent)
}

// Detects if device is in standalone mode
const isInStandaloneMode = () =>
	"standalone" in window.navigator && window.navigator.standalone

// Checks if should display install popup notification:
if (isIos() && !isInStandaloneMode()) {
	iosInstallMessage.value = true
}

window.addEventListener("beforeinstallprompt", (e) => {
	// Prevent the mini-infobar from appearing on mobile
	e.preventDefault()
	// Stash the event so it can be triggered later.
	deferredPrompt.value = e
	if (isIos() && !isInStandaloneMode()) {
		iosInstallMessage.value = true
	} else {
		showDialog.value = true
	}
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
