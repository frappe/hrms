<template>
	<div class="bg-white border rounded-lg p-4 flex">
		<div class="flex items-center">
			<FeatherIcon name="calendar" class="h-6 w-6 text-gray-400 mr-2" />
			<span class="text-2xl">Full Schedule</span>
		</div>
		<div class="ml-auto space-x-2 flex">
			<div v-for="filter in filters" class="w-40">
				<Autocomplete
					:placeholder="filter.placeholder"
					:options="filter.options"
					v-model="filter.model"
					:class="!filter.options.length && 'pointer-events-none'"
				/>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { reactive, watch } from "vue";
import { FeatherIcon, Autocomplete, createListResource } from "frappe-ui";

interface Filter {
	placeholder: string;
	options: string[];
	model: { value: string } | null;
}

interface Filters {
	company: Filter;
	department: Filter;
	branch: Filter;
	shift_type: Filter;
}

const filters: Filters = reactive({
	company: { placeholder: "Company", options: [], model: { value: "" } },
	department: { placeholder: "Department", options: [], model: { value: "" } },
	branch: { placeholder: "Branch", options: [], model: { value: "" } },
	shift_type: { placeholder: "Shift Type", options: [], model: { value: "" } },
});

watch(
	() => filters.company.model,
	(val) => {
		if (val) {
			departments.filters = { company: val.value };
			departments.fetch();
		} else {
			filters.department.model = null;
			filters.department.options = [];
		}
	},
);

// RESOURCES

const getFilterOptions = (doctype: string, filter: Filter) => {
	createListResource({
		doctype: doctype,
		fields: ["name"],
		onSuccess: (data: { name: string }[]) => {
			filter.options = data.map((item) => item.name);
		},
		auto: true,
	});
};

const departments = createListResource({
	doctype: "Department",
	fields: ["name"],
	onSuccess: (data: { name: string }[]) => {
		filters.department.model = { value: "" };
		filters.department.options = data.map((item) => item.name);
	},
});

getFilterOptions("Company", filters.company);
getFilterOptions("Branch", filters.branch);
getFilterOptions("Shift Type", filters.shift_type);
</script>
