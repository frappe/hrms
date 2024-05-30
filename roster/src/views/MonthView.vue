<template>
	<div class="px-12 py-6 space-y-6">
		<div class="flex items-center">
			<FeatherIcon name="calendar" class="h-7 w-7 text-gray-500 mr-3" />
			<span class="font-semibold text-2xl mr-1">Month View</span>
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
				class="ml-auto"
			/>
		</div>
		<div class="bg-white rounded-lg border p-4">
			<MonthViewHeader
				:firstOfMonth="firstOfMonth"
				@updateFilters="updateFilters"
				@addToMonth="addToMonth"
			/>
			<MonthViewTable
				ref="monthViewTable"
				:firstOfMonth="firstOfMonth"
				:employees="employees.data || []"
				:employeeFilters="employeeFilters"
				:shiftTypeFilter="shiftTypeFilter"
			/>
		</div>
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

import { dayjs, raiseToast } from "../utils";
import MonthViewTable from "../components/MonthViewTable.vue";
import MonthViewHeader from "../components/MonthViewHeader.vue";
import ShiftAssignmentDialog from "../components/ShiftAssignmentDialog.vue";

export type EmployeeFilters = {
	[K in "status" | "company" | "department" | "branch" | "designation"]?: string;
};

const monthViewTable = ref<InstanceType<typeof MonthViewTable>>();
const showShiftAssignmentDialog = ref(false);
const firstOfMonth = ref(dayjs().date(1).startOf("D"));
const shiftTypeFilter = ref("");
const employeeFilters = reactive<EmployeeFilters>({
	status: "Active",
});

const addToMonth = (change: number) => {
	firstOfMonth.value = firstOfMonth.value.add(change, "M");
};

const updateFilters = (newFilters: EmployeeFilters & { shift_type: string }) => {
	let employeeUpdated = false;
	(Object.entries(newFilters) as [keyof EmployeeFilters | "shift_type", string][]).forEach(
		([key, value]) => {
			if (key === "shift_type") {
				shiftTypeFilter.value = value;
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
	auto: true,
	onError(error: { messages: string[] }) {
		raiseToast("error", error.messages[0]);
	},
});
</script>
