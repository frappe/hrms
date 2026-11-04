<script setup>
import { computed, inject } from "vue";
import { Avatar } from "frappe-ui";
import { leave_label } from "../utils.js";

const props = defineProps({
	node: { type: Object, required: true },
});

const __ = window.__;
const chart = inject("org_chart");
const on_leave = computed(() => leave_label(props.node.leave));
const selected = computed(() => chart.selected.value === props.node.id);
</script>

<template>
	<button
		type="button"
		:data-node="node.id"
		class="flex w-52 items-center gap-2.5 rounded-5 px-3 py-2.5 text-left shadow-sm transition-colors"
		:class="selected ? 'bg-surface-gray-2' : 'bg-surface-elevation-1 hover:bg-surface-gray-1'"
		:aria-pressed="selected"
		@click="chart.select(node.id)"
	>
		<span class="relative flex shrink-0">
			<Avatar :image="node.image" :label="node.name" size="lg" />
			<span
				v-if="on_leave"
				class="absolute -bottom-0.5 -right-0.5 rounded-full bg-surface-base p-0.5"
				:title="on_leave"
				:aria-label="on_leave"
			>
				<span class="block size-2 rounded-full bg-surface-blue-5" />
			</span>
		</span>
		<span class="min-w-0 flex-1">
			<span class="flex items-center gap-1.5">
				<span class="truncate text-base text-ink-gray-8">{{ node.name }}</span>
				<span v-if="node.id === chart.me.value" class="shrink-0 text-sm text-ink-gray-5">
					{{ __("You") }}
				</span>
			</span>
			<span v-if="node.designation" class="block truncate text-sm text-ink-gray-5">
				{{ node.designation }}
			</span>
		</span>
	</button>
</template>
