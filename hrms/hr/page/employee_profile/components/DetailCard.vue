<script setup>
import PropertyRow from "./PropertyRow.vue";

// One private section: a titled card of label and value rows, or what the default slot puts in
// their place while the card is edited
defineProps({
	title: { type: String, required: true },
	// [{ label, icon, value, href? }], a row with an href links its value
	rows: { type: Array, default: () => [] },
});
</script>

<template>
	<section>
		<div class="mb-2 flex min-h-8 items-center gap-2">
			<h2 class="text-base-semibold text-ink-gray-9">{{ title }}</h2>
			<div class="ml-auto flex items-center gap-1">
				<slot name="actions" />
			</div>
		</div>
		<div class="rounded-5 border border-outline-gray-1 px-4 py-2">
			<slot>
				<PropertyRow v-for="row in rows" :key="row.label" v-bind="row" />
			</slot>
		</div>
	</section>
</template>
