<template>
	<div
		class="grid gap-x-3 gap-y-0.5 border-b border-outline-gray-1 py-1.5 last:border-0 last:pb-0 first:pt-0 sm:grid-cols-[7.5rem_minmax(0,1fr)] sm:items-baseline"
	>
		<dt class="text-base text-ink-gray-5">{{ label }}</dt>
		<dd class="min-w-0 text-p-base" :class="valueClass">
			<slot>
				<span v-if="isEmpty" class="italic text-ink-gray-4">Not set</span>
				<span v-else :class="nums && 'nums'">{{ value }}</span>
			</slot>
			<!-- locked values stay at full contrast: greying out reads as broken -->
			<FeatherIcon
				v-if="locked"
				name="lock"
				class="ml-1 inline h-3 w-3 shrink-0 align-[-1px] text-ink-gray-4"
			/>
		</dd>
	</div>
</template>

<script setup>
import { computed } from "vue";
import { FeatherIcon } from "frappe-ui";

const props = defineProps({
	label: String,
	value: [String, Number],
	locked: Boolean,
	nums: Boolean,
});

const isEmpty = computed(
	() => props.value === null || props.value === undefined || props.value === "",
);
const valueClass = computed(() => (props.locked ? "text-ink-gray-7" : "text-ink-gray-8"));
</script>
