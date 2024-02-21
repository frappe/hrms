<template>
	<Dialog
		:options="{
			title: notificationTitle,
			message: notificationBody,
			size: 'lg',
		}"
		v-model="showDialog"
		@close="() => (showDialog = false)"
	/>
</template>

<script setup>
import { ref, onMounted } from "vue"
import { Dialog } from "frappe-ui"

const showDialog = ref(false)
const notificationTitle = ref("")
const notificationBody = ref("")

onMounted(() => {
	window.frappePushNotification.onMessage((payload) => {
		notificationTitle.value = payload.data.title
		notificationBody.value = payload.data.body
		showDialog.value = true
	})
})
</script>
