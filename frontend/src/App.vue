<template>
	<ion-app>
		<Menu/>
		<ion-router-outlet id="main-content" />
	</ion-app>
</template>

<script>
import { IonApp, IonRouterOutlet } from "@ionic/vue"
import { defineComponent } from "vue"

import Menu from "@/components/Menu.vue"

export default defineComponent({
	name: "App",
	components: {
		IonApp,
		IonRouterOutlet,
		Menu,
	},
})
</script>
