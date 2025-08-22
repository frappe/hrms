<template>
	<div class="px-12 py-8 space-y-8">
		<div class="flex items-center">
			<FeatherIcon name="calendar" class="h-7 w-7 text-gray-500 mr-2.5" />
			<span class="font-semibold text-2xl text-gray-500 mr-2">Roster:</span>
			<span class="font-semibold text-2xl">Month View</span>
			<div class="ml-auto space-x-2.5">
				<Dropdown
					:options="VIEW_OPTIONS"
					:button="{
						label: 'View',
						iconRight: 'chevron-down',
						size: 'md',
					}"
				>
				</Dropdown>
				<Dropdown
					:options="[
						{
							label: 'Shift Assignment',
							onClick: () => {
								showShiftAssignmentDialog = true;
							},
						},
					]"
					:button="{
						label: 'Create',
						variant: 'solid',
						iconRight: 'chevron-down',
						size: 'md',
					}"
				/>
			</div>
		</div>
		<MonthViewHeader
			:firstOfMonth="firstOfMonth"
			@updateFilters="updateFilters"
			@addToMonth="addToMonth"
		/>
		<MonthViewTable
			v-if="isCompanySelected"
			ref="monthViewTable"
			:firstOfMonth="firstOfMonth"
			:employees="employees.data || []"
			:employeeFilters="employeeFilters"
			:shiftFilters="shiftFilters"
		/>
		<div v-else class="py-40 text-center">Please select a company.</div>
	</div>
	<ShiftAssignmentDialog
		v-model="showShiftAssignmentDialog"
		:isDialogOpen="showShiftAssignmentDialog"
		:employees="employees.data"
		@fetchEvents="
			monthViewTable?.events.fetch();
			showShiftAssignmentDialog = false;
		"
	/>
</template>

<script setup lang="ts">
import { ref, reactive } from "vue";
import { Dropdown, FeatherIcon, createListResource } from "frappe-ui";

import { dayjs, goTo, raiseToast } from "../utils";
import MonthViewTable from "../components/MonthViewTable.vue";
import MonthViewHeader from "../components/MonthViewHeader.vue";
import ShiftAssignmentDialog from "../components/ShiftAssignmentDialog.vue";

export type EmployeeFilters = {
	[K in "status" | "company" | "department" | "branch" | "designation"]?: string;
};
export type ShiftFilters = {
	[K in "shift_type" | "shift_location"]?: string;
};

const monthViewTable = ref<InstanceType<typeof MonthViewTable>>();
const isCompanySelected = ref(false);
const showShiftAssignmentDialog = ref(false);
const firstOfMonth = ref(dayjs().date(1).startOf("D"));
const employeeFilters = reactive<EmployeeFilters>({
	status: "Active",
});
const shiftFilters = reactive<ShiftFilters>({});

const VIEW_OPTIONS = [
	"Shift Type",
	"Shift Location",
	"Shift Assignment",
	"Shift Schedule",
	"Shift Schedule Assignment",
].map((label) => ({
	label,
	onClick: () => goTo(`/app/${label.toLowerCase().split(" ").join("-")}`),
}));

const addToMonth = (change: number) => {
	firstOfMonth.value = firstOfMonth.value.add(change, "M");
};

const updateFilters = (newFilters: EmployeeFilters & ShiftFilters) => {
	isCompanySelected.value = !!newFilters.company;
	if (!isCompanySelected.value) return;
	let employeeUpdated = false;
	(Object.entries(newFilters) as [keyof EmployeeFilters | keyof ShiftFilters, string][]).forEach(
		([key, value]) => {
			if (["shift_type", "shift_location"].includes(key)) {
				if (value) shiftFilters[key] = value;
				else delete shiftFilters[key];
				return;
			}

			if (value) employeeFilters[key] = value;
			else delete employeeFilters[key];
			employeeUpdated = true;
		},
	);
	if (employeeUpdated) employees.fetch();
};

// RESOURCES

const employees = createListResource({
	doctype: "Employee",
	fields: ["name", "employee_name", "designation", "image"],
	filters: employeeFilters,
	pageLength: 99999,
	onError(error: { messages: string[] }) {
		raiseToast("error", error.messages[0]);
	},
});
</script>
