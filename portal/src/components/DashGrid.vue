<template>
	<!-- the two-column dashboard archetype: act on the left, read on the right -->
	<div class="grid items-start gap-3.5" :class="gridClass">
		<div class="flex min-w-0 flex-col gap-3.5"><slot name="main" /></div>
		<div class="flex min-w-0 flex-col gap-3.5"><slot name="side" /></div>
	</div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
	ratio: { type: String, default: "wide" },
});

const gridClass = computed(() =>
	props.ratio === "even"
		? "grid-cols-1 lg:grid-cols-2"
		: "grid-cols-1 lg:grid-cols-[minmax(0,1.6fr)_minmax(0,1fr)]",
);
</script>
