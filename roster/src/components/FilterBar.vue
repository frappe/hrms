<template>
	<div class="bg-white border rounded-lg p-4 flex">
		<div class="flex items-center">
			<FeatherIcon name="calendar" class="h-6 w-6 text-gray-400 mr-2" />
			<span class="text-2xl">Full Schedule</span>
		</div>
		<div class="ml-auto space-x-2 flex">
			<div v-for="[key, value] of Object.entries(filters)" :key="key" class="w-40">
				<Autocomplete
					:placeholder="key"
					:options="value.options"
					v-model="value.model"
					:class="!value.options.length && 'pointer-events-none'"
				/>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { reactive, watch } from "vue";
import { FeatherIcon, Autocomplete, createListResource } from "frappe-ui";

import { FilterDoctype } from "../pages/FullSchedule.vue";

const emit = defineEmits<{
	(e: "updateFilters", newFilters: { [K in FilterDoctype]: string }): void;
}>();

const filters: {
	[K in FilterDoctype]: {
		options: string[];
		model?: { value: string } | null;
	};
} = reactive({
	Company: { options: [], model: { value: "" } },
	Department: { options: [], model: { value: "" } },
	Branch: { options: [], model: { value: "" } },
	"Shift Type": { options: [], model: { value: "" } },
});

watch(
	() => filters.Company.model,
	(val) => {
		if (val?.value) return getFilterOptions("Department", { company: val.value });
		else {
			filters.Department.model = null;
			filters.Department.options = [];
		}
	},
);

watch(filters, (val) => {
	const newFilters = {
		Company: val.Company.model?.value || "",
		Department: val.Department.model?.value || "",
		Branch: val.Branch.model?.value || "",
		"Shift Type": val["Shift Type"].model?.value || "",
	};

	emit("updateFilters", newFilters);
});

// RESOURCES

const getFilterOptions = (doctype: FilterDoctype, listFilters: { company?: string } = {}) => {
	createListResource({
		doctype: doctype,
		fields: ["name"],
		filters: listFilters,
		onSuccess: (data: { name: string }[]) => {
			filters[doctype].model = { value: "" };
			filters[doctype].options = data.map((item) => item.name);
		},
		auto: true,
	});
};

getFilterOptions("Company");
getFilterOptions("Branch");
getFilterOptions("Shift Type");
</script>
