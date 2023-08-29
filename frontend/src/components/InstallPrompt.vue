<template>
	<!-- Install PWA dialog -->
	<Dialog
		:options="{
			title: 'Install Frappe HR',
			message:
				'Get the app on your device for easy access & a better experience!',
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
				class="mt-[calc(100vh-15rem)] flex flex-col gap-2 mx-2 rounded-xl py-5 bg-blue-50 shadow-xl"
			>
				<div
					class="flex flex-row text-center items-center justify-between mb-1 px-3"
				>
					<span class="text-lg text-gray-900 font-bold">
						Install Frappe HR
					</span>
					<span class="inline-flex items-baseline">
						<FeatherIcon
							name="x"
							class="ml-auto h-4 w-4 text-gray-700"
							@click="iosInstallMessage = false"
						/>
					</span>
				</div>
				<div class="text-sm text-gray-800 px-3">
					<span class="flex flex-col gap-1">
						<span>
							Get the app on your iPhone for easy access & a better experience
						</span>
						<span class="inline-flex items-start whitespace-nowrap">
							<span>Tap&nbsp;</span>
							<FeatherIcon name="share" class="h-4 w-4 text-blue-600" />
							<span>&nbsp;and then "Add to Home Screen"</span>
						</span>
					</span>
				</div>
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
