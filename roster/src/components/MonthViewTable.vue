<template>
	<div class="rounded-lg border overflow-x-auto">
		<table class="border-separate border-spacing-0">
			<thead>
				<tr>
					<!-- Employee Search -->
					<th>
						<Autocomplete
							:options="employeeSearchOptions"
							v-model="employeeSearch"
							placeholder="Search Employee"
						/>
					</th>

					<!-- Day/Date Row -->
					<th v-for="(day, idx) in daysOfMonth" :key="idx" :class="{ 'border-l': idx }">
						{{ day.dayName }} {{ dayjs(day.date).format("DD") }}
					</th>
				</tr>
			</thead>
			<tbody>
				<tr v-for="employee in employees.data" :key="employee.name">
					<!-- Employee Column -->
					<td
						v-if="!employeeSearch?.value || employeeSearch?.value === employee?.name"
						class="border-t"
					>
						<div class="flex">
							<Avatar
								:label="employee.employee_name"
								:image="employee.image"
								size="2xl"
							/>
							<div class="flex flex-col ml-2 my-0.5 truncate">
								<div class="truncate text-base">
									{{ employee.employee_name }}
								</div>
								<div class="mt-auto text-xs text-gray-500 truncate">
									{{ employee.designation }}
								</div>
							</div>
						</div>
					</td>

					<!-- Events -->
					<td
						v-if="!employeeSearch?.value || employeeSearch?.value === employee?.name"
						v-for="(day, idx) in daysOfMonth"
						:key="idx"
						class="border-t"
						:class="{
							'border-l': idx,
							'align-top': events.data?.[employee.name]?.[day.date],
						}"
						@mouseover="hoveredCell = { employee: employee.name, date: day.date }"
						@mouseleave="hoveredCell = { employee: '', date: '' }"
					>
						<!-- Holiday -->
						<div
							v-if="events.data?.[employee.name]?.[day.date]?.name"
							class="rounded border-2 border-gray-300 bg-gray-50 px-2 py-1"
						>
							<div class="truncate mb-1">Holiday</div>
							<div class="text-xs text-gray-500">
								{{ events.data?.[employee.name]?.[day.date]?.["description"] }}
							</div>
						</div>

						<!-- Shifts -->
						<div v-else class="flex flex-col space-y-1.5">
							<div
								v-for="shift in events.data?.[employee.name]?.[day.date]"
								class="rounded border-2 border-gray-300 hover:border-gray-400 active:bg-gray-200 px-2 py-1 cursor-pointer"
								:class="shift.status === 'Active' ? 'bg-gray-50' : 'border-dashed'"
								@click="
									shiftAssignment = shift.name;
									showShiftAssignmentDialog = true;
								"
							>
								<div class="truncate mb-1">{{ shift["shift_type"] }}</div>
								<div class="text-xs text-gray-500">
									{{ shift["start_time"] }} - {{ shift["end_time"] }}
								</div>
							</div>

							<!-- Add Shift -->
							<Button
								variant="outline"
								icon="plus"
								class="border-2 active:bg-gray-200 w-full"
								:class="
									hoveredCell.employee === employee.name &&
									hoveredCell.date === day.date
										? 'visible'
										: 'invisible'
								"
								@click="
									shiftAssignment = null;
									showShiftAssignmentDialog = true;
								"
							/>
						</div>
					</td>
				</tr>
			</tbody>
		</table>
	</div>

	<ShiftAssignmentDialog
		v-model="showShiftAssignmentDialog"
		:isDialogOpen="showShiftAssignmentDialog"
		:shiftAssignmentName="shiftAssignment"
		:selectedCell="hoveredCell"
		:employees="employees.data"
		@fetchEvents="
			events.fetch();
			showShiftAssignmentDialog = false;
		"
	/>
</template>

<script setup lang="ts">
import { ref, computed, watch } from "vue";
import { Avatar, Autocomplete, createListResource, createResource } from "frappe-ui";
import { Dayjs } from "dayjs";

import dayjs from "../utils/dayjs";
import { FilterField } from "./MonthViewHeader.vue";
import ShiftAssignmentDialog from "./ShiftAssignmentDialog.vue";

interface Holiday {
	name: string;
	description: string;
	weekly_off: 0 | 1;
}

interface HolidayWithDate extends Holiday {
	holiday_date: string;
}

type Shift = {
	[K in "name" | "shift_type" | "status" | "start_time" | "end_time"]: string;
};

interface ShiftAssignment extends Shift {
	start_date: string;
	end_date: string;
}

const props = defineProps<{
	firstOfMonth: Dayjs;
	filters: { [K in FilterField]: string };
}>();

const employeeSearch = ref({ value: "", label: "" });
const shiftAssignment = ref();
const showShiftAssignmentDialog = ref(false);
const hoveredCell = ref({ employee: "", date: "" });

const employeeFilters = computed(() => {
	const filters: Record<string, string> = {
		status: "Active",
	};
	Object.entries(props.filters).forEach(([key, value]) => {
		if (key !== "shift_type" && value) filters[key] = value;
	});
	return filters;
});

const daysOfMonth = computed(() => {
	const daysOfMonth = [];
	for (let i = 1; i <= props.firstOfMonth.daysInMonth(); i++) {
		const date = props.firstOfMonth.date(i);
		daysOfMonth.push({
			dayName: date.format("ddd"),
			date: date.format("YYYY-MM-DD"),
		});
	}
	return daysOfMonth;
});

const employeeSearchOptions = computed(() => {
	return employees?.data?.map((employee: { name: string; employee_name: string }) => ({
		value: employee.name,
		label: `${employee.name}: ${employee.employee_name}`,
	}));
});

watch(
	() => props.firstOfMonth,
	() => events.fetch(),
);

watch(props.filters, () => {
	employees.filters = employeeFilters.value;
	employees.fetch();
	events.fetch();
});

// RESOURCES

const employees = createListResource({
	doctype: "Employee",
	fields: ["name", "employee_name", "designation", "image"],
	filters: employeeFilters.value,
	auto: true,
});

const events = createResource({
	url: "hrms.api.roster.get_events",
	makeParams() {
		return {
			month_start: props.firstOfMonth.format("YYYY-MM-DD"),
			month_end: props.firstOfMonth.endOf("month").format("YYYY-MM-DD"),
			employee_filters: employeeFilters.value,
			shift_filters: props.filters.shift_type
				? { shift_type: props.filters.shift_type }
				: {},
		};
	},
	transform: (data: Record<string, (ShiftAssignment | HolidayWithDate)[]>) => {
		// convert employee -> events to employee -> date -> holiday/shifts
		const mappedData: Record<string, Record<string, Holiday | Shift[]>> = {};
		for (const employee in data) {
			mappedData[employee] = {};
			for (let d = 1; d <= props.firstOfMonth.daysInMonth(); d++) {
				const date = props.firstOfMonth.date(d);
				const key = date.format("YYYY-MM-DD");
				for (const event of Object.values(data[employee])) {
					// holiday
					if ("holiday_date" in event) {
						if (date.isSame(event.holiday_date))
							mappedData[employee][key] = {
								name: event.name,
								description: event.description,
								weekly_off: event.weekly_off,
							};
					}

					// shift
					else if (
						dayjs(event.start_date).isSameOrBefore(date) &&
						(dayjs(event.end_date).isSameOrAfter(date) || !event.end_date)
					) {
						if (!Array.isArray(mappedData[employee][key]))
							mappedData[employee][key] = [];
						mappedData[employee][key].push({
							name: event.name,
							shift_type: event.shift_type,
							status: event.status,
							start_time: event.start_time.split(":").slice(0, 2).join(":"),
							end_time: event.end_time.split(":").slice(0, 2).join(":"),
						});
					}
				}

				// sort shifts by start time
				if (Array.isArray(mappedData[employee][key]))
					mappedData[employee][key].sort((a: Shift, b: Shift) =>
						a.start_time.localeCompare(b.start_time),
					);
			}
		}
		return mappedData;
	},
	auto: true,
});
</script>

<style>
th,
td {
	@apply max-w-32 min-w-32 p-1.5;
	font-size: 0.875rem;
}

th:first-child,
td:first-child {
	@apply sticky left-0 max-w-48 min-w-48 bg-white border-r;
}
</style>
