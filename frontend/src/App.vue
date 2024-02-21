<template>
	<ion-app>
		<ion-router-outlet id="main-content" />
		<Toasts />

		<InstallPrompt />
		<FrappeNotification />
	</ion-app>
</template>

<script setup>
import { IonApp, IonRouterOutlet } from "@ionic/vue"

import { Toasts } from "frappe-ui"

import InstallPrompt from "@/components/InstallPrompt.vue"
import FrappeNotification from "@/components/FrappeNotification.vue"
</script>
