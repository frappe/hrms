<script setup>
defineProps({ items: { type: Array, required: true } });
</script>

<!-- inline items so text-wrap: balance evens out the rows instead of leaving one alone -->
<template>
	<div class="text-balance pt-2 text-center text-sm leading-6 text-ink-gray-6">
		<span
			v-for="item in items"
			:key="item.label"
			class="mx-2 inline-flex items-center gap-1.5 whitespace-nowrap"
		>
			<span class="size-2 shrink-0 rounded-full" :style="{ backgroundColor: item.color }" />
			<span>{{ item.label }}</span>
			<span v-if="item.count != null" class="text-ink-gray-5">{{ item.count }}</span>
		</span>
	</div>
</template>
