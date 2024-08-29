<template>
	<div class="flex mb-4">
		<!-- Month Change -->
		<Button icon="chevron-left" variant="ghost" @click="emit('addToMonth', -1)" />
		<span class="px-1 w-24 text-center my-auto font-medium">
			{{ props.firstOfMonth.format("MMM") }} {{ firstOfMonth.format("YYYY") }}
		</span>
		<Button icon="chevron-right" variant="ghost" @click="emit('addToMonth', 1)" />

		<!-- Filters -->
		<div class="ml-auto px-2 overflow-x-clip">
			<div
				class="ml-auto space-x-2 flex transition-all"
				:class="showFilters ? 'w-full' : 'w-0 overflow-hidden'"
			>
				<div v-for="[key, value] of Object.entries(filters)" :key="key" class="w-40">
					<FormControl
						type="autocomplete"
						:placeholder="toTitleCase(key)"
						:options="value.options"
						v-model="value.model"
						:disabled="!value.options.length"
					/>
				</div>
				<Button
					icon="x"
					@click="Object.values(filters).forEach((d) => (d.model = null))"
				/>
			</div>
		</div>
		<Button
			:icon="showFilters ? 'chevrons-right' : 'chevrons-left'"
			variant="ghost"
			@click="showFilters = !showFilters"
		/>
	</div>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from "vue";
import { FormControl, createListResource } from "frappe-ui";
import { Dayjs } from "dayjs";

import { raiseToast } from "../utils";

export type FilterField = "company" | "department" | "branch" | "designation" | "shift_type";

const props = defineProps<{
	firstOfMonth: Dayjs;
}>();

const emit = defineEmits<{
	(e: "addToMonth", change: number): void;
	(e: "updateFilters", newFilters: { [K in FilterField]: string }): void;
}>();

const showFilters = ref(true);

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
		designation: val.designation.model?.value || "",
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
		auto: true,
		onSuccess: (data: { name: string }[]) => {
			filters[field].model = { value: "" };
			filters[field].options = data.map((item) => item.name);
		},
		onError(error: { messages: string[] }) {
			raiseToast("error", error.messages[0]);
		},
	});
};

["company", "branch", "designation", "shift_type"].forEach((field) =>
	getFilterOptions(field as FilterField),
);
</script>
