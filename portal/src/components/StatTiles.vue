<template>
	<div class="grid gap-3" :class="gridClass">
		<div
			v-for="tile in tiles"
			:key="tile.label"
			class="flex flex-col gap-0.5 rounded-lg border border-outline-gray-1 bg-surface-white p-3"
		>
			<span class="text-base text-ink-gray-5">
				{{ tile.label }}
			</span>
			<span class="nums text-xl font-semibold leading-tight text-ink-gray-9">
				{{ tile.value }}
			</span>
			<Progress v-if="tile.pct !== undefined" class="mt-1.5" :value="tile.pct" size="md" />
			<span v-if="tile.hint" class="mt-0.5 text-sm text-ink-gray-5">{{ tile.hint }}</span>
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue";
import { Progress } from "frappe-ui";

const props = defineProps({ tiles: { type: Array, default: () => [] } });

const gridClass = computed(() =>
	props.tiles.length === 3 ? "grid-cols-1 sm:grid-cols-3" : "grid-cols-2 lg:grid-cols-4",
);
</script>
