<template>
	<div class="px-12 py-6 space-y-6">
		<div class="bg-white rounded-lg border p-4">
			<MonthViewHeader
				:firstOfMonth="firstOfMonth"
				@updateFilters="updateFilters"
				@addToMonth="addToMonth"
			/>
			<MonthViewTable :firstOfMonth="firstOfMonth" :filters="filters" />
		</div>
	</div>
</template>

<script setup lang="ts">
import { ref, reactive } from "vue";

import dayjs from "../utils/dayjs";
import MonthViewTable from "../components/MonthViewTable.vue";
import MonthViewHeader from "../components/MonthViewHeader.vue";

const firstOfMonth = ref(dayjs().date(1).startOf("D"));

const filters = reactive({
	company: "",
	department: "",
	branch: "",
	designation: "",
	shift_type: "",
});

const addToMonth = (change: number) => {
	firstOfMonth.value = firstOfMonth.value.add(change, "M");
};

const updateFilters = (newFilters: typeof filters) => {
	Object.assign(filters, newFilters);
};
</script>
