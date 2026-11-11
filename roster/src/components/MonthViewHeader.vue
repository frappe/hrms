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
		<div class="ml-auto space-x-2.5 flex">
			<div v-for="[key, value] of visibleFilters" :key="key" class="w-40">
				<FormControl
					type="autocomplete"
					:placeholder="toTitleCase(key)"
					:options="value.options"
					v-model="value.model"
					:disabled="!value.options.length"
				/>
			</div>
			<Button icon="x" @click="Object.values(filters).forEach((d) => (d.model = null))" />
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed, reactive, watch } from "vue";
import { FormControl, createResource, createListResource } from "frappe-ui";
import { Dayjs } from "dayjs";

import { raiseToast } from "../utils";

export type FilterField =
	| "company"
	| "department"
	| "branch"
	| "designation"
	| "shift_type"
	| "shift_location";

const props = defineProps<{
	firstOfMonth: Dayjs;
}>();

const emit = defineEmits<{
	(e: "addToMonth", change: number): void;
	(e: "updateFilters", newFilters: { [K in FilterField]: string }): void;
}>();

const filters: {
	[K in FilterField]: {
		options: string[];
		model?: { value: string } | null;
	};
} = reactive({
	company: { options: [], model: null },
	department: { options: [], model: null },
	branch: { options: [], model: null },
	designation: { options: [], model: null },
	shift_type: { options: [], model: null },
	shift_location: { options: [], model: null },
});

const visibleFilters = computed(() =>
	Object.entries(filters).filter(([key]) =>
		(permittedFilterDoctypes.data || []).includes(toTitleCase(key)),
	),
);

watch(
	() => filters.company.model,
	(val) => {
		if (val?.value && isPermitted("department"))
			getFilterOptions("department", { company: val.value });
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
		designation: val.designation.model?.value || "",
		shift_type: val.shift_type.model?.value || "",
		shift_location: val.shift_location.model?.value || "",
	};
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
	onSuccess: () => permittedFilterDoctypes.fetch(),
});

// skip filters whose doctype the user cannot list, instead of raising permission errors
const permittedFilterDoctypes = createResource({
	url: "hrms.api.roster.get_permitted_filter_doctypes",
	onSuccess: () => {
		(["company", "branch", "designation", "shift_type", "shift_location"] as FilterField[])
			.filter(isPermitted)
			.forEach((field) => getFilterOptions(field));
	},
});

const isPermitted = (field: FilterField) =>
	(permittedFilterDoctypes.data || []).includes(toTitleCase(field));

const getFilterOptions = (field: FilterField, listFilters: { company?: string } = {}) => {
	createListResource({
		doctype: toTitleCase(field),
		fields: ["name"],
		filters: listFilters,
		pageLength: 100,
		auto: true,
		onSuccess: (data: { name: string }[]) => {
			const value = field === "company" ? defaultCompany.data : "";
			filters[field].model = { value };
			filters[field].options = data.map((item) => item.name);
		},
		onError(error: { messages: string[] }) {
			raiseToast("error", error.messages[0]);
		},
	});
};
</script>
