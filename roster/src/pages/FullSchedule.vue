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

export type FilterField = "company" | "department" | "branch" | "shift_type";

const filters = reactive({ company: "", department: "", branch: "", shift_type: "" });

const updateFilters = (newFilters: typeof filters) => {
	Object.assign(filters, newFilters);
};
</script>
