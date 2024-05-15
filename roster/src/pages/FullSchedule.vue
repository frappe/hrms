<template>
	<div class="px-12 py-6 space-y-6">
		<FilterBar @updateFilters="updateFilters" />
		<MonthView :filters="filters" />
	</div>
</template>

<script setup lang="ts">
import { reactive } from "vue";

import FilterBar from "../components/FilterBar.vue";
import MonthView from "../components/MonthView.vue";

export type FilterDoctype = "Company" | "Department" | "Branch" | "Shift Type";

const filters = reactive({ Company: "", Department: "", Branch: "", "Shift Type": "" });

const updateFilters = (newFilters: typeof filters) => {
	Object.assign(filters, newFilters);
};
</script>
