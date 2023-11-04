<template>
	<ion-header>
		<ion-toolbar>
			<ion-title>{{ file.file_name }} - File Preview</ion-title>
			<ion-buttons slot="end">
				<ion-button @click="modalController.dismiss()">Close</ion-button>
			</ion-buttons>
		</ion-toolbar>
	</ion-header>
	<ion-content>
		<div class="bg-white h-full w-full overflow-auto touch-pinch-zoom">
			<img
				v-if="isImageFile(file.file_name)"
				:src="file.file_url"
				class="h-auto"
			/>
			<iframe v-else :src="file.file_url" class="w-full h-full"></iframe>
		</div>
	</ion-content>
</template>

<script setup>
import {
	IonHeader,
	IonToolbar,
	IonContent,
	IonButtons,
	IonTitle,
	IonButton,
	modalController,
} from "@ionic/vue"

const props = defineProps({
	file: {
		type: Object,
		required: true,
	},
})

const isImageFile = (filename) => {
	return /\.(gif|jpg|jpeg|tiff|png|svg)$/i.test(filename)
}
</script>
