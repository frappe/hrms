<template>
	<ion-page>
		<ion-content :fullscreen="true">
			<FormView doctype="Leave Application" />
		</ion-content>
	</ion-page>
</template>

<script setup>
import { IonPage, IonContent } from "@ionic/vue"
import { FeatherIcon } from "frappe-ui"

import FormView from "@/components/FormView.vue"
</script>
