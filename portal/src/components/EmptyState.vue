<template>
	<div class="flex flex-col items-start gap-1.5 py-2">
		<p class="text-base text-ink-gray-5">{{ message }}</p>
		<Button
			v-if="action"
			class="-ml-2"
			variant="ghost"
			:label="action"
			@click="$emit('action')"
		/>
	</div>
</template>

<script setup>
import { Button } from "frappe-ui";
defineProps({ message: String, action: String });
defineEmits(["action"]);
</script>
