<script setup>
defineProps({
	title: { type: String, required: true },
	subtitle: { type: String, default: undefined },
});
</script>

<!-- A chart header of our own, styled as frappe-ui's, so the subtitle can wrap -->
<template>
	<div>
		<div class="truncate text-p-base text-ink-gray-8">{{ title }}</div>
		<p v-if="subtitle" class="text-p-sm text-ink-gray-5">{{ subtitle }}</p>
	</div>
</template>
