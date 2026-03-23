<template>
	<ion-page>
		<ion-content class="ion-padding">
			<div class="flex h-screen w-screen flex-col items-center justify-center bg-white text-center">
				<FrappeHRLogo class="mb-4 h-8 w-8" />
				<div class="text-3xl font-semibold text-gray-900">
					{{ __("Redirecting to Ameide Sign In") }}
				</div>
				<div class="mt-4 text-sm text-gray-600">
					{{ __("If nothing happens, use the button below.") }}
				</div>
				<Button variant="solid" class="mt-6" @click="redirectNow()">
					{{ __("Continue") }}
				</Button>
			</div>
		</ion-content>
	</ion-page>
</template>

<script setup>
import { IonPage, IonContent } from "@ionic/vue"
import { onMounted } from "vue"
import { Button } from "frappe-ui"

import FrappeHRLogo from "@/components/icons/FrappeHRLogo.vue"
import { buildAmeideOidcLoginHref, redirectToAmeideOidc } from "@/utils/auth"

const redirectNow = () => {
	redirectToAmeideOidc("/login")
}

onMounted(() => {
	window.location.replace(buildAmeideOidcLoginHref("/login"))
})
</script>
