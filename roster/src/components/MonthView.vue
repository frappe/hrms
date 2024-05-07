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
			<table>
				<thead>
					<tr>
						<th></th>
						<th v-for="day in daysOfMonth" :key="day" class="border-l">
							{{ day.name }} {{ day.no }}
						</th>
					</tr>
				</thead>
				<tbody>
					<tr v-for="employee in employees.data" :key="employee.name">
						<td class="border-t align-middle">
							<div class="flex">
								<Avatar
									:label="employee.employee_name"
									:image="employee.image"
									size="2xl"
								/>
								<div class="flex flex-col ml-2 my-1 text-xs truncate">
									<div class="truncate">
										{{ employee.employee_name }}
									</div>
									<div class="mt-auto text-gray-500 truncate">
										{{ employee.designation }}
									</div>
								</div>
							</div>
						</td>
						<td v-for="day in daysOfMonth" :key="day" class="border-l border-t">
							<div
								v-if="shifts.data?.[employee.name]?.[day.no]"
								class="flex flex-col space-y-1.5"
							>
								<div
									v-for="shift in shifts.data[employee.name][day.no]"
									class="rounded border-2 px-2 py-1 cursor-pointer"
									:class="
										shift.status === 'Active' ? 'bg-gray-50' : 'border-dashed'
									"
									@click="
										selectedShiftAssignment = shift.name;
										showShiftAssignmentDialog = true;
									"
								>
									<div class="mb-1">{{ shift["shiftType"] }}</div>
									<div class="text-xs text-gray-500">
										{{ shift["startTime"] }} - {{ shift["endTime"] }}
									</div>
								</div>
							</div>
						</td>
					</tr>
				</tbody>
			</table>
		</div>
	</div>
	<Dialog
		v-model="showShiftAssignmentDialog"
		:options="{ title: `Shift Assignment ${selectedShiftAssignment}`, size: '4xl' }"
	>
		<template #body-content>
			<div class="grid grid-cols-2 gap-6">
				<FormControl
					:type="'text'"
					:disabled="true"
					label="Employee"
					:value="shiftAssignment.data?.employee"
				/>
				<FormControl
					:type="'text'"
					:disabled="true"
					label="Company"
					:value="shiftAssignment.data?.company"
				/>
				<FormControl
					:type="'text'"
					:disabled="true"
					label="Employee Name"
					:value="shiftAssignment.data?.employee_name"
				/>
				<FormControl
					:type="'date'"
					:disabled="true"
					label="Start Date"
					:value="shiftAssignment.data?.start_date"
				/>
				<FormControl
					:type="'text'"
					:disabled="true"
					label="Shift Type"
					:value="shiftAssignment.data?.shift_type"
				/>
				<FormControl
					id="end_date"
					:type="'date'"
					label="End Date"
					v-model="shiftAssignmentEndDate"
				/>
				<FormControl
					id="staus"
					:type="'select'"
					:options="['Active', 'Inactive']"
					label="Status"
					v-model="shiftAssignmentStatus"
				/>
				<FormControl
					:type="'text'"
					:disabled="true"
					label="Department"
					:value="shiftAssignment.data?.department"
				/>
			</div>
		</template>
		<template #actions>
			<div class="flex">
				<Button class="ml-auto" @click="showShiftAssignmentDialog = false"> Close </Button>
				<Button variant="solid" class="ml-2" :disabled="isUpdateButtonDisabled">
					Update
				</Button>
			</div>
		</template>
	</Dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from "vue";
import dayjs from "../utils/dayjs";
import { Avatar, Dialog, FormControl, createResource } from "frappe-ui";

const firstOfMonth = ref(dayjs().date(1));
const selectedShiftAssignment = ref("");
const showShiftAssignmentDialog = ref(false);
const shiftAssignmentStatus = ref("");
const shiftAssignmentEndDate = ref("");

const daysOfMonth = computed(() => {
	const daysOfMonth = [];
	for (let i = 1; i <= firstOfMonth.value.daysInMonth(); i++) {
		const date = firstOfMonth.value.date(i);
		daysOfMonth.push({ no: date.format("DD"), name: date.format("ddd") });
	}
	return daysOfMonth;
});
const isUpdateButtonDisabled = computed(() => {
	return (
		!shiftAssignment.data ||
		(shiftAssignment.data?.status === shiftAssignmentStatus.value &&
			shiftAssignment.data?.end_date === shiftAssignmentEndDate.value)
	);
});

watch(firstOfMonth, () => fetchShifts());
watch(showShiftAssignmentDialog, () => {
	if (showShiftAssignmentDialog.value) return;
	shiftAssignmentStatus.value = shiftAssignment.data.status;
	shiftAssignmentEndDate.value = shiftAssignment.data.end_date;
});
watch(selectedShiftAssignment, () => {
	shiftAssignment.params = { name: selectedShiftAssignment.value };
	shiftAssignment.fetch();
});

const fetchShifts = () => {
	shifts.params = {
		month_start: firstOfMonth.value.format("YYYY-MM-DD"),
		month_end: firstOfMonth.value.endOf("month").format("YYYY-MM-DD"),
	};
	shifts.fetch();
};

// RESOURCES

const employees = createResource({
	url: "hrms.api.roster.get_employees",
	auto: true,
});

const shifts = createResource({
	url: "hrms.api.roster.get_shifts",
	transform: (data) => {
		// convert employee -> shift assignments to employee -> day -> shifts
		const mappedData = {};
		for (const employee in data) {
			mappedData[employee] = {};
			for (let d = 1; d <= firstOfMonth.value.daysInMonth(); d++) {
				const date = firstOfMonth.value.date(d);
				const key = date.format("DD");
				for (const assignment of data[employee]) {
					if (
						dayjs(assignment.start_date).isSameOrBefore(date) &&
						(dayjs(assignment.end_date).isSameOrAfter(date) || !assignment.end_date)
					) {
						if (!mappedData[employee][key]) mappedData[employee][key] = [];
						mappedData[employee][key].push({
							name: assignment.name,
							shiftType: assignment.shift_type,
							status: assignment.status,
							startTime: assignment.start_time.split(":").slice(0, 2).join(":"),
							endTime: assignment.end_time.split(":").slice(0, 2).join(":"),
						});
					}
				}
				// sort shifts by start time
				if (mappedData[employee][key])
					mappedData[employee][key].sort((a, b) =>
						a.startTime.localeCompare(b.startTime),
					);
			}
		}
		return mappedData;
	},
});

const shiftAssignment = createResource({
	url: "hrms.api.roster.get_shift_assignment",
	onSuccess: (data) => {
		shiftAssignmentStatus.value = data.status;
		shiftAssignmentEndDate.value = data.end_date;
	},
});

fetchShifts();
</script>

<style>
th,
td {
	max-width: 10rem;
	min-width: 10rem;
	padding: 0.375rem;
	vertical-align: top;
	font-size: 0.875rem;
}
</style>
