<template>
	<div
		class="rounded-lg border overflow-auto max-h-[45rem]"
		:class="loading && 'animate-pulse pointer-events-none'"
	>
		<table class="border-separate border-spacing-0">
			<thead>
				<tr class="sticky top-0 bg-white z-10">
					<!-- Employee Search -->
					<th class="p-2 border-b">
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
						class="font-medium border-b"
						:class="{ 'border-l': idx }"
					>
						{{ day.dayName }} {{ dayjs(day.date).format("DD") }}
					</th>
				</tr>
			</thead>
			<tbody>
				<tr v-for="(employee, rowIdx) in employees" :key="employee.name">
					<!-- Employee Column -->
					<td
						v-if="
							!employeeSearch?.length ||
							employeeSearch?.some((item) => item.value === employee?.name)
						"
						class="px-2 py-7 z-[5]"
						:class="{ 'border-t': rowIdx }"
					>
						<div class="flex" :class="!employee.designation && 'items-center'">
							<Avatar
								:label="employee.employee_name"
								:image="employee.image"
								size="2xl"
							/>
							<div class="flex flex-col ml-2 my-0.5 truncate">
								<div class="truncate text-base font-medium">
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
						v-for="(day, colIdx) in daysOfMonth"
						:key="colIdx"
						class="p-1.5"
						:class="{
							'border-l': colIdx,
							'border-t': rowIdx,
							'align-top': events.data?.[employee.name]?.[day.date],
							'align-middle bg-blue-50':
								events.data?.[employee.name]?.[day.date]?.holiday,
							'align-middle bg-pink-50':
								events.data?.[employee.name]?.[day.date]?.leave,
							'bg-gray-50':
								dropCell.employee === employee.name &&
								dropCell.date === day.date &&
								!(
									isHolidayOrLeave(employee.name, day.date) ||
									hasSameShift(employee.name, day.date)
								),
						}"
						@mouseenter="
							hoveredCell.employee = employee.name;
							hoveredCell.date = day.date;
						"
						@mouseleave="
							hoveredCell.employee = '';
							hoveredCell.date = '';
						"
						@dragover.prevent
						@dragenter="
							dropCell.employee = employee.name;
							dropCell.date = day.date;
						"
						@drop="
							() => {
								if (
									!(
										isHolidayOrLeave(employee.name, day.date) ||
										hasSameShift(employee.name, day.date)
									)
								) {
									loading = true;
									swapShift.submit();
								}
							}
						"
					>
						<!-- Holiday -->
						<div
							v-if="events.data?.[employee.name]?.[day.date]?.holiday"
							class="blocked-cell"
						>
							<div
								v-html="
									events.data[employee.name][day.date].weekly_off
										? '<strong>WO</strong>'
										: events.data[employee.name][day.date].description
								"
							></div>
						</div>

						<!-- Leave -->
						<div
							v-else-if="events.data?.[employee.name]?.[day.date]?.leave"
							class="blocked-cell"
						>
							{{ events.data[employee.name][day.date].leave_type }}
						</div>

						<!-- Shifts -->
						<div v-else class="flex flex-col space-y-1.5 translate-x-0 translate-y-0">
							<div
								v-for="shift in events.data?.[employee.name]?.[day.date]"
								@mouseenter="
									hoveredCell.shift = shift.name;
									hoveredCell.shift_type = shift.shift_type;
									hoveredCell.shift_location = shift.shift_location;
									hoveredCell.shift_status = shift.status;
								"
								@mouseleave="
									hoveredCell.shift = '';
									hoveredCell.shift_type = '';
									hoveredCell.shift_location = '';
									hoveredCell.shift_status = '';
								"
								@dragenter="dropCell.shift = shift.name"
								@dragleave="dropCell.shift = ''"
								:draggable="true"
								@dragstart="
									(event) => {
										if (event.dataTransfer) {
											event.dataTransfer.effectAllowed = 'move';
										}
									}
								"
								@dragend="
									if (!loading) dropCell = { employee: '', date: '', shift: '' };
								"
								class="rounded border-2 p-2 cursor-pointer"
								:class="[
									shift.status === 'Inactive' && 'border-dashed',
									dropCell.employee === employee.name &&
										dropCell.date === day.date &&
										dropCell.shift === shift.name &&
										!hasSameShift(employee.name, day.date) &&
										'scale-105',
									hoveredCell.employee === employee.name &&
										hoveredCell.date === day.date &&
										hoveredCell.shift === shift.name &&
										dropCell.employee &&
										'opacity-0',
								]"
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
								<div
									class="truncate mb-1.5 pointer-events-none text-base font-medium"
								>
									{{ shift["shift_type"] }}
								</div>
								<div class="text-xs text-gray-500 pointer-events-none space-y-1.5">
									<div class="flex items-center space-x-1">
										<FeatherIcon
											name="clock"
											class="stroke-gray-400"
											style="
												 {
													height: 0.82rem;
													width: 0.82rem;
												}
											"
										/>
										<span>
											{{ shift["start_time"] }} - {{ shift["end_time"] }}
										</span>
									</div>
									<div
										v-if="shift['shift_location']"
										class="flex items-center space-x-1"
									>
										<FeatherIcon
											name="map-pin"
											class="stroke-gray-400"
											style="
												 {
													height: 0.82rem;
													width: 0.82rem;
												}
											"
										/>
										<span>{{ shift["shift_location"] }}</span>
									</div>
								</div>
							</div>

							<!-- Add Shift -->
							<Button
								variant="outline"
								icon="plus"
								class="border-2 active:bg-white w-full"
								:class="
									hoveredCell.employee === employee.name &&
									hoveredCell.date === day.date &&
									!dropCell.employee
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
		:employees="employees"
		@fetchEvents="
			events.fetch();
			showShiftAssignmentDialog = false;
		"
	/>
</template>

<script setup lang="ts">
import { ref, computed, watch } from "vue";
import colors from "tailwindcss/colors";
import { Avatar, Autocomplete, FeatherIcon, createResource } from "frappe-ui";
import { Dayjs } from "dayjs";

import { dayjs, raiseToast } from "../utils";
import { EmployeeFilters, ShiftFilters } from "../views/MonthView.vue";
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
	[K in "name" | "shift_type" | "status" | "start_time" | "end_time" | "shift_location"]: string;
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
	employees: {
		[K in "name" | "employee_name" | "designation" | "image"]: string;
	}[];
	employeeFilters: { [K in keyof EmployeeFilters]?: string };
	shiftFilters: { [K in keyof ShiftFilters]?: string };
}>();

const loading = ref(true);
const employeeSearch = ref<{ value: string; label: string }[]>();
const shiftAssignment = ref<string>();
const showShiftAssignmentDialog = ref(false);
const hoveredCell = ref({
	employee: "",
	date: "",
	shift: "",
	shift_type: "",
	shift_location: "",
	shift_status: "",
});
const dropCell = ref({ employee: "", date: "", shift: "" });

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
	return props.employees.map((employee: { name: string; employee_name: string }) => ({
		value: employee.name,
		label: `${employee.name}: ${employee.employee_name}`,
	}));
});

watch(
	() => [props.firstOfMonth, props.employeeFilters, props.shiftFilters],
	() => {
		loading.value = true;
		events.fetch();
	},
	{ deep: true },
);

watch(loading, (val) => {
	if (!val) dropCell.value = { employee: "", date: "", shift: "" };
});

const isHolidayOrLeave = (employee: string, day: string) =>
	events.data?.[employee]?.[day]?.holiday || events.data?.[employee]?.[day]?.leave;

const hasSameShift = (employee: string, day: string) =>
	Array.isArray(events.data?.[employee]?.[day]) &&
	events.data?.[employee]?.[day].some(
		(shift: Shift) =>
			shift.shift_type === hoveredCell.value.shift_type &&
			shift.shift_location === hoveredCell.value.shift_location &&
			shift.status === hoveredCell.value.shift_status,
	);

// RESOURCES

const events = createResource({
	url: "hrms.api.roster.get_events",
	auto: true,
	makeParams() {
		return {
			month_start: props.firstOfMonth.format("YYYY-MM-DD"),
			month_end: props.firstOfMonth.endOf("month").format("YYYY-MM-DD"),
			employee_filters: props.employeeFilters,
			shift_filters: props.shiftFilters,
		};
	},
	onSuccess() {
		loading.value = false;
	},
	onError(error: { messages: string[] }) {
		raiseToast("error", error.messages[0]);
	},
	transform: (data: Events) => {
		const mappedEvents: MappedEvents = {};
		for (const employee in data) {
			mapEventsToDates(data, mappedEvents, employee);
		}
		return mappedEvents;
	},
});
defineExpose({ events });

const swapShift = createResource({
	url: "hrms.api.roster.swap_shift",
	makeParams() {
		return {
			src_shift: hoveredCell.value.shift,
			src_date: hoveredCell.value.date,
			tgt_employee: dropCell.value.employee,
			tgt_date: dropCell.value.date,
			tgt_shift: dropCell.value.shift,
		};
	},
	onSuccess: () => {
		raiseToast("success", `Shift ${dropCell.value.shift ? "swapped" : "moved"} successfully!`);
		events.fetch();
	},
	onError(error: { messages: string[] }) {
		loading.value = false;
		raiseToast("error", error.messages[0]);
	},
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
			shift_location: event.shift_location,
			status: event.status,
			start_time: dayjs(event.start_time, "hh:mm:ss").format("HH:mm"),
			end_time: dayjs(event.end_time, "hh:mm:ss").format("HH:mm"),
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
	@apply max-w-36 min-w-36;
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
