<template>
	<div class="rounded-lg border overflow-x-auto">
		<table class="border-separate border-spacing-0">
			<thead>
				<tr>
					<!-- Employee Search -->
					<th class="p-2">
						<Autocomplete
							:options="employeeSearchOptions"
							v-model="employeeSearch"
							placeholder="Search Employee"
							:multiple="true"
						/>
					</th>

					<!-- Day/Date Row -->
					<th
						v-for="(day, idx) in daysOfMonth"
						:key="idx"
						class="font-medium"
						:class="{ 'border-l': idx }"
					>
						{{ day.dayName }} {{ dayjs(day.date).format("DD") }}
					</th>
				</tr>
			</thead>
			<tbody>
				<tr v-for="employee in employees.data" :key="employee.name">
					<!-- Employee Column -->
					<td
						v-if="
							!employeeSearch?.length ||
							employeeSearch?.some((item) => item.value === employee?.name)
						"
						class="border-t px-2 py-7"
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
						v-if="
							!employeeSearch?.length ||
							employeeSearch?.some((item) => item.value === employee?.name)
						"
						v-for="(day, idx) in daysOfMonth"
						:key="idx"
						class="border-t p-1.5"
						:class="{
							'border-l': idx,
							'align-top': events.data?.[employee.name]?.[day.date],
							'align-middle bg-gray-50':
								events.data?.[employee.name]?.[day.date]?.holiday,
							'align-middle bg-blue-50':
								events.data?.[employee.name]?.[day.date]?.leave,
						}"
						@mouseover="
							hoveredCell.employee = employee.name;
							hoveredCell.date = day.date;
						"
						@mouseleave="
							hoveredCell.employee = '';
							hoveredCell.date = '';
						"
					>
						<!-- Holiday -->
						<div
							v-if="events.data?.[employee.name]?.[day.date]?.holiday"
							class="blocked-cell"
						>
							{{
								events.data[employee.name][day.date].weekly_off
									? "WO"
									: events.data[employee.name][day.date].description
							}}
						</div>

						<!-- Leave -->
						<div
							v-else-if="events.data?.[employee.name]?.[day.date]?.leave"
							class="blocked-cell"
						>
							{{ events.data[employee.name][day.date].leave_type }}
						</div>

						<!-- Shifts -->
						<div v-else class="flex flex-col space-y-1.5">
							<div
								v-for="shift in events.data?.[employee.name]?.[day.date]"
								@mouseover="hoveredCell.shift = shift.name"
								@mouseleave="hoveredCell.shift = ''"
								class="rounded border-2 px-2 py-1 cursor-pointer"
								:class="shift.status === 'Inactive' && 'border-dashed'"
								:style="{
									borderColor:
										hoveredCell.shift === shift.name &&
										hoveredCell.date === day.date
											? colors[shift.color as Color][300]
											: colors[shift.color as Color][200],
									backgroundColor:
										shift.status === 'Active'
											? colors[shift.color as Color][50]
											: 'white',
								}"
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
								class="border-2 active:bg-white w-full"
								:class="
									hoveredCell.employee === employee.name &&
									hoveredCell.date === day.date
										? 'visible'
										: 'invisible'
								"
								@click="
									shiftAssignment = '';
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
		:selectedCell="{ employee: hoveredCell.employee, date: hoveredCell.date }"
		:employees="employees.data"
		@fetchEvents="
			events.fetch();
			showShiftAssignmentDialog = false;
		"
	/>
</template>

<script setup lang="ts">
import { ref, computed, watch } from "vue";
import colors from "tailwindcss/colors";
import { Avatar, Autocomplete, createListResource, createResource } from "frappe-ui";
import { Dayjs } from "dayjs";

import dayjs from "../utils/dayjs";
import { FilterField } from "./MonthViewHeader.vue";
import ShiftAssignmentDialog from "./ShiftAssignmentDialog.vue";

interface Holiday {
	holiday: string;
	description: string;
	weekly_off: 0 | 1;
}

interface HolidayWithDate extends Holiday {
	holiday_date: string;
}

interface Leave {
	leave: string;
	leave_type: string;
}

interface LeaveApplication extends Leave {
	from_date: string;
	to_date: string;
}

type Color =
	| "blue"
	| "cyan"
	| "fuchsia"
	| "green"
	| "lime"
	| "orange"
	| "pink"
	| "red"
	| "violet"
	| "yellow";

type Shift = {
	[K in "name" | "shift_type" | "status" | "start_time" | "end_time"]: string;
} & {
	color: Color;
};

interface ShiftAssignment extends Shift {
	start_date: string;
	end_date: string;
}

type Events = Record<string, (HolidayWithDate | LeaveApplication | ShiftAssignment)[]>;
type MappedEvents = Record<string, Record<string, Holiday | Leave | Shift[]>>;

const props = defineProps<{
	firstOfMonth: Dayjs;
	filters: { [K in FilterField]: string };
}>();

const employeeSearch = ref<{ value: string; label: string }[]>();
const shiftAssignment = ref<string>();
const showShiftAssignmentDialog = ref(false);
const hoveredCell = ref({ employee: "", date: "", shift: "" });

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
	transform: (data: Events) => {
		const mappedEvents: MappedEvents = {};
		for (const employee in data) {
			mapEventsToDates(data, mappedEvents, employee);
		}
		return mappedEvents;
	},
	auto: true,
});

const mapEventsToDates = (data: Events, mappedEvents: MappedEvents, employee: string) => {
	mappedEvents[employee] = {};
	for (let d = 1; d <= props.firstOfMonth.daysInMonth(); d++) {
		const date = props.firstOfMonth.date(d);
		const key = date.format("YYYY-MM-DD");

		for (const event of Object.values(data[employee])) {
			let result: Holiday | Leave | undefined;
			if ("holiday" in event) {
				result = handleHoliday(event, date);
				if (result) {
					mappedEvents[employee][key] = result;
					break;
				}
			} else if ("leave" in event) {
				result = handleLeave(event, date);
				if (result) {
					mappedEvents[employee][key] = result;
					break;
				}
			} else handleShifts(event, date, mappedEvents, employee, key);
		}
		sortShiftsByStartTime(mappedEvents, employee, key);
	}
};

const handleHoliday = (event: HolidayWithDate, date: Dayjs) => {
	if (date.isSame(event.holiday_date)) {
		return {
			holiday: event.holiday,
			description: event.description,
			weekly_off: event.weekly_off,
		};
	}
};

const handleLeave = (event: LeaveApplication, date: Dayjs) => {
	if (dayjs(event.from_date).isSameOrBefore(date) && dayjs(event.to_date).isSameOrAfter(date))
		return {
			leave: event.leave,
			leave_type: event.leave_type,
		};
};

const handleShifts = (
	event: ShiftAssignment,
	date: Dayjs,
	mappedEvents: MappedEvents,
	employee: string,
	key: string,
) => {
	if (
		dayjs(event.start_date).isSameOrBefore(date) &&
		(dayjs(event.end_date).isSameOrAfter(date) || !event.end_date)
	) {
		if (!Array.isArray(mappedEvents[employee][key])) mappedEvents[employee][key] = [];
		mappedEvents[employee][key].push({
			name: event.name,
			shift_type: event.shift_type,
			status: event.status,
			start_time: event.start_time.split(":").slice(0, 2).join(":"),
			end_time: event.end_time.split(":").slice(0, 2).join(":"),
			color: event.color.toLowerCase() as Color,
		});
	}
};

const sortShiftsByStartTime = (mappedEvents: MappedEvents, employee: string, key: string) => {
	if (Array.isArray(mappedEvents[employee][key]))
		mappedEvents[employee][key].sort((a: Shift, b: Shift) =>
			a.start_time.localeCompare(b.start_time),
		);
};
</script>

<style>
th,
td {
	@apply max-w-32 min-w-32;
	font-size: 0.875rem;
}

th:first-child,
td:first-child {
	@apply sticky left-0 max-w-64 min-w-64 bg-white border-r;
}

.blocked-cell {
	@apply text-sm text-gray-500 text-center p-2;
}
</style>
