<template>
	<Dialog
		:options="{
			title: props.options.title,
			message: props.options.message,
			actions: [
				{
					label: 'Confirm',
					variant: 'solid',
					onClick: props.options.action,
				},
			],
		}"
	>
	</Dialog>
</template>

<script setup lang="ts">
import { Dialog } from "frappe-ui";

const props = defineProps<{
	options: { title: string; message: string; action: () => void };
}>();
</script>
