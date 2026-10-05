<template>
	<div
		class="flex flex-col items-center justify-center gap-2 rounded-5 border border-dashed border-outline-gray-2 px-4 py-8 text-center"
	>
		<div
			v-if="icon"
			class="flex size-10 items-center justify-center rounded-full bg-surface-gray-2 text-ink-gray-5"
		>
			<span :class="[icon, 'size-5']" aria-hidden="true" />
		</div>
		<p class="text-base-medium text-ink-gray-8">{{ title }}</p>
		<p v-if="description" class="max-w-sm text-p-base text-ink-gray-5">{{ description }}</p>
	</div>
</template>

<script setup lang="ts">
defineProps<{ title: string; icon?: string; description?: string }>();
</script>
