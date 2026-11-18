<script setup>
import { computed } from "vue";

const props = defineProps({
	label: { type: String, default: undefined },
	items: { type: Array, required: true },
	order: { type: Array, required: true },
});

// frappe-ui sorts readings by value; a stack reads in its series order instead
const series = computed(() =>
	props.items
		.filter((item) => item.kind === "series")
		.sort((a, b) => props.order.indexOf(a.name) - props.order.indexOf(b.name)),
);
</script>

<!-- The body of frappe-ui's default chart tooltip -->
<template>
	<div v-if="label" class="mb-2 text-p-sm text-ink-gray-5">{{ label }}</div>
	<div class="flex flex-col gap-1.5">
		<div
			v-for="item in series"
			:key="item.name"
			class="flex items-center justify-between gap-5 text-p-sm"
		>
			<span class="flex min-w-0 items-center gap-2">
				<span class="size-2 shrink-0 rounded-1" :style="{ backgroundColor: item.color }" />
				<span class="truncate text-ink-gray-6">{{ item.label }}</span>
			</span>
			<span class="shrink-0 text-p-sm-semibold tabular-nums text-ink-gray-8">
				{{ item.formattedValue }}
			</span>
		</div>
	</div>
</template>
