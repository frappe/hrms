<template>
	<ion-app>
		<Menu />
		<ion-router-outlet id="main-content" />
		<Toasts />
	</ion-app>
</template>

<script setup>
import { IonApp, IonRouterOutlet } from "@ionic/vue"
import { defineComponent } from "vue"

import { Toasts } from "frappe-ui"

import Menu from "@/components/Menu.vue"
</script>
