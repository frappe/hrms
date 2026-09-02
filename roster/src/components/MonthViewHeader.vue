<template>
	<div class="flex items-center">
		<!-- Month Change -->
		<div class="flex items-center bg-gray-50 rounded-md space-x-0.5">
			<Button icon="chevron-left" variant="ghost" @click="emit('addToMonth', -1)" />
			<span class="w-32 text-center font-medium text-base">
				{{ props.firstOfMonth.format("MMMM") }}, {{ firstOfMonth.format("YYYY") }}
			</span>
			<Button icon="chevron-right" variant="ghost" @click="emit('addToMonth', 1)" />
		</div>

		<!-- Filters -->
		<div class="ml-auto flex flex-wrap justify-end gap-2.5">
			<div v-for="[key, filter] of Object.entries(filters)" :key="key" class="filter-item w-40">
				<FormControl
					v-if="filter.kind === 'text'"
					type="text"
					:placeholder="toTitleCase(key)"
					v-model="filter.model"
				/>
				<FormControl
					v-else-if="filter.kind === 'select'"
					type="select"
					:placeholder="toTitleCase(key)"
					:options="filter.options"
					v-model="filter.model"
				/>
				<FormControl
					v-else
					type="autocomplete"
					:placeholder="toTitleCase(key)"
					:options="filter.options"
					v-model="filter.model"
					:disabled="!filter.options.length"
				/>
			</div>
			<Button icon="x" @click="Object.values(filters).forEach((d) => (d.model = null))" />
		</div>
	</div>
</template>

<style scoped>
/* frappe-ui's Autocomplete placeholder span lacks a truncate class, so long
   placeholders (e.g. "Employment Type") wrap to two lines and misalign the
   filter row's height. Force it to a single truncated line here instead. */
.filter-item :deep(button span) {
	white-space: nowrap;
	overflow: hidden;
	text-overflow: ellipsis;
}
</style>

<script setup lang="ts">
import { reactive, watch } from "vue";
import { FormControl, createResource, createListResource } from "frappe-ui";
import { Dayjs } from "dayjs";

import { raiseToast } from "../utils";

export type FilterField =
	| "company"
	| "department"
	| "branch"
	| "designation"
	| "shift_type"
	| "shift_location"
	| "reports_to"
	| "grade"
	| "employment_type"
	| "station"
	| "production_line"
	| "employee_number"
	| "location";

type AutocompleteFilter = {
	kind: "autocomplete";
	doctype: string;
	options: string[];
	model?: { value: string } | null;
};
type SelectFilter = { kind: "select"; options: string[]; model?: string | null };
type TextFilter = { kind: "text"; options: string[]; model?: string | null };
type Filter = AutocompleteFilter | SelectFilter | TextFilter;

const props = defineProps<{
	firstOfMonth: Dayjs;
}>();

const emit = defineEmits<{
	(e: "addToMonth", change: number): void;
	(e: "updateFilters", newFilters: { [K in FilterField]: string }): void;
}>();

const FILTER_CONFIG: Record<FilterField, Omit<Filter, "options" | "model">> = {
	company: { kind: "autocomplete", doctype: "Company" },
	department: { kind: "autocomplete", doctype: "Department" },
	branch: { kind: "autocomplete", doctype: "Branch" },
	designation: { kind: "autocomplete", doctype: "Designation" },
	shift_type: { kind: "autocomplete", doctype: "Shift Type" },
	shift_location: { kind: "autocomplete", doctype: "Shift Location" },
	reports_to: { kind: "autocomplete", doctype: "Employee" },
	grade: { kind: "autocomplete", doctype: "Employee Grade" },
	employment_type: { kind: "autocomplete", doctype: "Employment Type" },
	station: { kind: "text" },
	production_line: { kind: "text" },
	employee_number: { kind: "text" },
	location: { kind: "select", options: ["FACTORY", "PLANT", "OFFICE"] },
};

const filters: { [K in FilterField]: Filter } = reactive(
	Object.fromEntries(
		(Object.keys(FILTER_CONFIG) as FilterField[]).map((field) => [
			field,
			{ ...FILTER_CONFIG[field], options: FILTER_CONFIG[field].options || [], model: null },
		]),
	),
) as { [K in FilterField]: Filter };

watch(
	() => (filters.company as AutocompleteFilter).model,
	(val) => {
		if (val?.value) getFilterOptions("department", { company: val.value });
		else {
			filters.department.model = null;
			filters.department.options = [];
		}
	},
);

watch(filters, (val) => {
	const newFilters = Object.fromEntries(
		(Object.keys(val) as FilterField[]).map((key) => {
			const filter = val[key];
			const value =
				filter.kind === "autocomplete"
					? (filter as AutocompleteFilter).model?.value || ""
					: (filter as SelectFilter | TextFilter).model || "";
			return [key, value];
		}),
	) as { [K in FilterField]: string };
	emit("updateFilters", newFilters);
});

const toTitleCase = (str: string) =>
	str
		.split("_")
		.map((s) => s.charAt(0).toUpperCase() + s.slice(1))
		.join(" ");

// RESOURCES

const defaultCompany = createResource({
	url: "hrms.api.roster.get_default_company",
	auto: true,
	onSuccess: () => {
		(Object.keys(FILTER_CONFIG) as FilterField[])
			.filter((field) => FILTER_CONFIG[field].kind === "autocomplete")
			.forEach((field) => getFilterOptions(field));
	},
});

const getFilterOptions = (field: FilterField, listFilters: { company?: string } = {}) => {
	const config = filters[field] as AutocompleteFilter;
	if (config.kind !== "autocomplete") return;

	createListResource({
		doctype: config.doctype,
		fields: ["name"],
		filters: listFilters,
		pageLength: 100,
		auto: true,
		onSuccess: (data: { name: string }[]) => {
			const value = field === "company" ? defaultCompany.data : "";
			(filters[field] as AutocompleteFilter).model = { value };
			filters[field].options = data.map((item) => item.name);
		},
		onError(error: { messages: string[] }) {
			raiseToast("error", error.messages[0]);
		},
	});
};
</script>
