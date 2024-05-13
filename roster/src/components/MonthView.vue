<template>
	<div class="bg-white rounded-lg border p-4">
		<!-- Header -->
		<div class="flex mb-4">
			<Button
				icon="chevron-left"
				variant="ghost"
				@click="firstOfMonth = firstOfMonth.subtract(1, 'M')"
			/>
			<span class="px-1 w-20 text-center my-auto">
				{{ firstOfMonth.format("MMM") }} '{{ firstOfMonth.format("YY") }}
			</span>
			<Button
				icon="chevron-right"
				variant="ghost"
				@click="firstOfMonth = firstOfMonth.add(1, 'M')"
			/>
		</div>

		<!-- Table -->
		<div class="rounded-lg border overflow-x-auto">
			<table class="border-separate border-spacing-0">
				<thead>
					<tr>
						<th />
						<th
							v-for="(day, idx) in daysOfMonth"
							:key="idx"
							:class="{ 'border-l': idx }"
						>
							{{ day.dayName }} {{ dayjs(day.date).format("DD") }}
						</th>
					</tr>
				</thead>
				<tbody>
					<tr v-for="employee in employees.data" :key="employee.name">
						<td class="border-t">
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
						<td
							v-for="(day, idx) in daysOfMonth"
							:key="idx"
							class="border-t"
							:class="{
								'border-l': idx,
								'align-top': shifts.data?.[employee.name]?.[day.date],
							}"
							@mouseover="hoveredCell = { employee: employee.name, date: day.date }"
							@mouseleave="hoveredCell = { employee: '', date: '' }"
						>
							<div class="flex flex-col space-y-1.5">
								<div
									v-for="shift in shifts.data?.[employee.name]?.[day.date]"
									class="rounded border-2 border-gray-300 hover:border-gray-400 active:bg-gray-200 px-2 py-1 cursor-pointer"
									:class="
										shift.status === 'Active' ? 'bg-gray-50' : 'border-dashed'
									"
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
	</div>
	<ShiftAssignmentDialog
		v-model="showShiftAssignmentDialog"
		:isDialogOpen="showShiftAssignmentDialog"
		:shiftAssignmentName="shiftAssignment"
		:selectedCell="hoveredCell"
		:employees="employees.data"
		@fetchShifts="
			shifts.fetch();
			showShiftAssignmentDialog = false;
		"
	/>
</template>

<script setup lang="ts">
import { ref, computed, watch } from "vue";
import dayjs from "../utils/dayjs";
import { Avatar, createListResource, createResource } from "frappe-ui";

import ShiftAssignmentDialog from "./ShiftAssignmentDialog.vue";

interface ShiftAssignment {
	name: string;
	shift_type: string;
	status: string;
	start_time: string;
	end_time: string;
}

const firstOfMonth = ref(dayjs().date(1).startOf("D"));
const shiftAssignment = ref();
const showShiftAssignmentDialog = ref(false);
const hoveredCell = ref({ employee: "", date: "" });

const daysOfMonth = computed(() => {
	const daysOfMonth = [];
	for (let i = 1; i <= firstOfMonth.value.daysInMonth(); i++) {
		const date = firstOfMonth.value.date(i);
		daysOfMonth.push({
			dayName: date.format("ddd"),
			date: date.format("YYYY-MM-DD"),
		});
	}
	return daysOfMonth;
});

watch(firstOfMonth, () => shifts.fetch());

// RESOURCES

const employees = createListResource({
	doctype: "Employee",
	fields: ["name", "employee_name", "designation", "image"],
	filters: { status: "Active" },
	auto: true,
});

const shifts = createResource({
	url: "hrms.api.roster.get_shifts",
	makeParams() {
		return {
			month_start: firstOfMonth.value.format("YYYY-MM-DD"),
			month_end: firstOfMonth.value.endOf("month").format("YYYY-MM-DD"),
		};
	},
	transform: (data: Record<string, ShiftAssignment>) => {
		// convert employee -> shift assignments to employee -> day -> shifts
		const mappedData: Record<string, Record<string, ShiftAssignment[]>> = {};
		for (const employee in data) {
			mappedData[employee] = {};
			for (let d = 1; d <= firstOfMonth.value.daysInMonth(); d++) {
				const date = firstOfMonth.value.date(d);
				const key = date.format("YYYY-MM-DD");
				for (const assignment of Object.values(data[employee])) {
					if (
						dayjs(assignment.start_date).isSameOrBefore(date) &&
						(dayjs(assignment.end_date).isSameOrAfter(date) || !assignment.end_date)
					) {
						if (!mappedData[employee][key]) mappedData[employee][key] = [];
						mappedData[employee][key].push({
							name: assignment.name,
							shift_type: assignment.shift_type,
							status: assignment.status,
							start_time: assignment.start_time.split(":").slice(0, 2).join(":"),
							end_time: assignment.end_time.split(":").slice(0, 2).join(":"),
						});
					}
				}
				// sort shifts by start time
				if (mappedData[employee][key])
					mappedData[employee][key].sort((a: ShiftAssignment, b: ShiftAssignment) =>
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
