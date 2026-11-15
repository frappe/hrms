<script setup>
defineProps({
	label: { type: String, required: true },
	formattedValue: { type: String, required: true },
	percent: { type: Number, default: undefined },
});

// as DonutChart prints a hovered slice's share
const formatPercent = (percent) => {
	if (!percent) return "0%";
	return percent < 1 ? "<1%" : `${Math.round(percent)}%`;
};
</script>

<!-- DonutChart's readout, but the caption never cuts -->
<template>
	<div class="flex w-full flex-col items-center text-center">
		<div class="whitespace-nowrap text-xl font-semibold tabular-nums text-ink-gray-8">
			{{ formattedValue }}
		</div>
		<!-- a hovered slice's share drops to its own line when the name fills the hole -->
		<div class="flex flex-wrap items-baseline justify-center gap-x-1 text-xs text-ink-gray-5">
			<span class="whitespace-nowrap">{{ label }}</span>
			<span v-if="percent !== undefined">{{ formatPercent(percent) }}</span>
		</div>
	</div>
</template>
