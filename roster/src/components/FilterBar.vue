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

interface Filter {
	options: string[];
	model: { value: string } | null;
}

interface Filters {
	Company: Filter;
	Department: Filter;
	Branch: Filter;
	"Shift Type": Filter;
}

const filters: Filters = reactive({
	Company: { options: [], model: { value: "" } },
	Department: { options: [], model: { value: "" } },
	Branch: { options: [], model: { value: "" } },
	"Shift Type": { options: [], model: { value: "" } },
});

watch(
	() => filters.Company.model,
	(val) => {
		if (val?.value) {
			getFilterOptions("Department", { company: val.value });
		} else {
			filters.Department.model = null;
			filters.Department.options = [];
		}
	},
);

// RESOURCES

const getFilterOptions = (
	doctype: "Company" | "Department" | "Branch" | "Shift Type",
	listFilters: { company?: string } = {},
) => {
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
