<template>
	<ion-app>
		<div class="flex h-full w-full">
			<DesktopSidebar v-if="showSidebar" />
			<div class="flex-1 relative overflow-hidden min-w-0">
				<ion-router-outlet id="main-content" />
			</div>
		</div>
		<Toasts />
		<InstallPrompt />
	</ion-app>
</template>

<script setup>
import { computed, onMounted } from "vue"
import { useRoute } from "vue-router"
import { IonApp, IonRouterOutlet } from "@ionic/vue"

import { Toasts } from "frappe-ui"

import DesktopSidebar from "@/components/DesktopSidebar.vue"
import InstallPrompt from "@/components/InstallPrompt.vue"
import { showNotification } from "@/utils/pushNotifications"

const route = useRoute()

// Only show the sidebar on authenticated pages
const GUEST_ROUTES = ["Login", "InvalidEmployee"]
const showSidebar = computed(() => !GUEST_ROUTES.includes(route.name))

onMounted(() => {
	window?.frappePushNotification?.onMessage((payload) => {
		showNotification(payload)
	})
})
</script>
