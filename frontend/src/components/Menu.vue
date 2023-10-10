<template>
	<ion-menu
		content-id="main-content"
		:swipe-gesture="false"
		:disabled="route.name === 'Login'"
	>
		<ion-content class="ion-padding">
			<div class="bg-white h-full">
				<div
					class="flex w-full items-center justify-between py-8 px-4 border-b"
				>
					<FrappeHRLogo />
				</div>
				<MenuLinks />
			</div>
		</ion-content>
	</ion-menu>
</template>

<script setup>
import { IonContent, IonMenu } from "@ionic/vue"

import MenuLinks from "@/components/MenuLinks.vue"
import FrappeHRLogo from "@/components/icons/FrappeHRLogo.vue"
import { useRoute } from "vue-router"

const route = useRoute()
</script>
