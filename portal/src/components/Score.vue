<template>
	<span v-if="!value" class="text-ink-gray-4">—</span>
	<span
		v-else
		class="nums"
		:class="strong ? 'font-semibold text-ink-gray-9' : 'text-ink-gray-6'"
	>
		{{ value }}<span class="text-ink-gray-4">/5</span>
	</span>
</template>

<script setup>
/** A score out of five. Every appraisal number in HRMS is on that scale. */
defineProps({
	value: { type: Number, default: 0 },
	strong: { type: Boolean, default: false },
});
</script>
