<template>
	<div class="bg-white border rounded-lg p-4 flex">
		<div class="flex items-center">
			<FeatherIcon name="calendar" class="h-6 w-6 text-gray-400 mr-2" />
			<span class="text-2xl">Full Schedule</span>
		</div>
		<div class="ml-auto space-x-2 flex">
			<div v-for="[key, value] of Object.entries(filters)" :key="key" class="w-40">
				<Autocomplete
					:placeholder="toTitleCase(key)"
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

import { FilterField } from "../pages/FullSchedule.vue";

const emit = defineEmits<{
	(e: "updateFilters", newFilters: { [K in FilterField]: string }): void;
}>();

const filters: {
	[K in FilterField]: {
		options: string[];
		model?: { value: string } | null;
	};
} = reactive({
	company: { options: [], model: { value: "" } },
	department: { options: [], model: { value: "" } },
	branch: { options: [], model: { value: "" } },
	shift_type: { options: [], model: { value: "" } },
});

watch(
	() => filters.company.model,
	(val) => {
		if (val?.value) return getFilterOptions("department", { company: val.value });
		else {
			filters.department.model = null;
			filters.department.options = [];
		}
	},
);

watch(filters, (val) => {
	const newFilters = {
		company: val.company.model?.value || "",
		department: val.department.model?.value || "",
		branch: val.branch.model?.value || "",
		shift_type: val.shift_type.model?.value || "",
	};

	emit("updateFilters", newFilters);
});

const toTitleCase = (str: string) =>
	str
		.split("_")
		.map((s) => s.charAt(0).toUpperCase() + s.slice(1))
		.join(" ");

// RESOURCES

const getFilterOptions = (field: FilterField, listFilters: { company?: string } = {}) => {
	createListResource({
		doctype: toTitleCase(field),
		fields: ["name"],
		filters: listFilters,
		onSuccess: (data: { name: string }[]) => {
			filters[field].model = { value: "" };
			filters[field].options = data.map((item) => item.name);
		},
		auto: true,
	});
};

getFilterOptions("company");
getFilterOptions("branch");
getFilterOptions("shift_type");
</script>
