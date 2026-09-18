<template>
	<div
		class="flex items-baseline justify-between gap-3 border-t border-outline-gray-2 px-3.5 py-2.5"
	>
		<span class="text-base text-ink-gray-5">{{ label }}</span>
		<span
			class="nums shrink-0 font-semibold text-ink-gray-9"
			:class="strong ? 'text-lg' : 'text-base'"
		>
			{{ value }}
		</span>
	</div>
</template>

<script setup>
defineProps({
	label: String,
	value: [String, Number],
	strong: Boolean,
});
</script>
