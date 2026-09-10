<template>
	<div class="flex flex-wrap items-end justify-between gap-3">
		<div class="min-w-0">
			<Breadcrumbs v-if="items.length" class="mb-0.5" :items="items" />
			<h1 v-if="title" class="truncate text-2xl-semibold text-ink-gray-9">
				{{ title }}
			</h1>
			<p v-if="subtitle" class="mt-0.5 text-base text-ink-gray-5">{{ subtitle }}</p>
		</div>
		<div v-if="$slots.actions" class="flex flex-wrap items-center gap-2">
			<slot name="actions" />
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue";
import { Breadcrumbs } from "frappe-ui";

const props = defineProps({
	title: String,
	subtitle: String,
	crumbs: Array,
});

// frappe-ui Breadcrumbs expects `route`, callers pass `to`
const items = computed(() => (props.crumbs || []).map((c) => ({ label: c.label, route: c.to })));
</script>
