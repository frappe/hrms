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
					<FrappeHRLogoType />
				</div>
				<MenuLinks />
			</div>
		</ion-content>
	</ion-menu>
</template>

<script setup>
import { IonContent, IonMenu } from "@ionic/vue"

import MenuLinks from "@/components/MenuLinks.vue"
import FrappeHRLogoType from "@/components/icons/FrappeHRLogoType.vue"
import { useRoute } from "vue-router"

const route = useRoute()
</script>
