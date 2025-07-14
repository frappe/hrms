<template>
	<Dialog :options="{ title: dialog.title, size: '4xl' }">
		<template #body-content>
			<div class="grid grid-cols-2 gap-6">
				<FormControl
					type="autocomplete"
					label="Employee"
					v-model="form.employee"
					:disabled="!!props.shiftAssignmentName"
					:options="employees"
				/>
				<FormControl type="text" label="Company" v-model="form.company" :disabled="true" />
				<FormControl
					type="text"
					label="Employee Name"
					v-model="form.employee_name"
					:disabled="true"
				/>
				<FormControl
					type="text"
					label="Department"
					v-model="form.department"
					:disabled="true"
				/>
				<Link
					doctype="Shift Type"
					label="Shift Type"
					v-model="form.shift_type"
					:disabled="!!props.shiftAssignmentName"
				/>
				<FormControl
					type="date"
					label="Start Date"
					v-model="form.start_date"
					:disabled="!!props.shiftAssignmentName"
				/>
				<Link
					doctype="Shift Location"
					label="Shift Location"
					v-model="form.shift_location"
					:disabled="!!props.shiftAssignmentName"
				/>
				<FormControl
					type="date"
					label="End Date"
					v-model="form.end_date"
					:disabled="!!props.shiftAssignmentName"
				/>
				<FormControl
					type="select"
					:options="['Active', 'Inactive']"
					label="Status"
					v-model="form.status"
				/>
			</div>

			<!-- Schedule Settings -->
			<div
				v-if="
					(!props.shiftAssignmentName && showShiftScheduleSettings) ||
					form.shift_schedule_assignment
				"
				class="mt-6 space-y-6"
			>
				<hr />
				<h4 class="font-semibold">Schedule Settings</h4>
				<div class="grid grid-cols-2 gap-6">
					<div class="space-y-1.5">
						<div class="text-xs text-gray-600">Repeat On Days</div>
						<div
							class="border rounded grid grid-flow-col h-7 justify-stretch overflow-clip"
						>
							<div
								v-for="(isSelected, day) of repeatOnDays"
								class="cursor-pointer flex flex-col"
								:class="{
									'border-r': day !== 'Sunday',
									'bg-gray-100 text-gray-500': !isSelected,
									'pointer-events-none': !!props.shiftAssignmentName,
								}"
								@click="repeatOnDays[day] = !repeatOnDays[day]"
							>
								<div class="text-center text-sm my-auto">
									{{ day.substring(0, 3) }}
								</div>
							</div>
						</div>
					</div>
					<FormControl
						type="select"
						:options="[
							'Every Week',
							'Every 2 Weeks',
							'Every 3 Weeks',
							'Every 4 Weeks',
						]"
						label="Frequency"
						v-model="frequency"
						:disabled="!!props.shiftAssignmentName"
					/>
				</div>
			</div>

			<Dialog
				v-model="showDeleteDialog"
				:options="{
					title: deleteDialogOptions.title,
					actions: [
						{
							label: 'Confirm',
							variant: 'solid',
							onClick: deleteDialogOptions.action,
						},
					],
				}"
			>
				<template #body-content>
					<div v-html="deleteDialogOptions.message" />
				</template>
			</Dialog>
		</template>
		<template #actions>
			<div class="flex space-x-3 justify-end">
				<Dropdown v-if="props.shiftAssignmentName" :options="actions">
					<Button size="md" label="Delete" class="w-28 text-red-600" />
				</Dropdown>
				<Button
					size="md"
					variant="solid"
					:disabled="dialog.actionDisabled"
					class="w-28"
					@click="dialog.action"
				>
					{{ dialog.button }}
				</Button>
			</div>
		</template>
	</Dialog>
</template>

<script setup lang="ts">
import { reactive, ref, computed, watch } from "vue";
import {
	DatePicker,
	Dialog,
	FormControl,
	Dropdown,
	createDocumentResource,
	createResource,
	createListResource,
} from "frappe-ui";
import Link from "./Link.vue";
import { dayjs, raiseToast } from "../utils";

type Status = "Active" | "Inactive";

type Form = {
	[K in
		| "company"
		| "employee_name"
		| "department"
		| "employee"
		| "shift_type"
		| "shift_location"]: string | { value: string; label?: string };
} & {
	start_date: string;
	end_date: string;
	status: Status | { value: Status; label?: Status };
	schedule?: string;
};

interface Props {
	isDialogOpen: boolean;
	shiftAssignmentName?: string;
	selectedCell?: {
		employee: string;
		date: string;
	};
	employees?: {
		name: string;
		employee_name: string;
	}[];
}

const props = withDefaults(defineProps<Props>(), {
	employees: () => [],
});

const emit = defineEmits<{
	(e: "fetchEvents"): void;
}>();

const formObject: Form = {
	employee: "",
	company: "",
	employee_name: "",
	department: "",
	shift_type: "",
	start_date: "",
	shift_location: "",
	end_date: "",
	status: "Active",
	shift_schedule_assignment: "",
};

const repeatOnDaysObject = {
	Monday: false,
	Tuesday: false,
	Wednesday: false,
	Thursday: false,
	Friday: false,
	Saturday: false,
	Sunday: false,
};

const form = reactive({ ...formObject });
const repeatOnDays = reactive({ ...repeatOnDaysObject });

const shiftAssignment = ref();
const selectedDate = ref();
const frequency = ref("Every Week");
const showDeleteDialog = ref(false);
const deleteDialogOptions = ref({ title: "", message: "", action: () => {} });

const dialog = computed(() => {
	if (props.shiftAssignmentName)
		return {
			title: `[${selectedDate.value}] Shift Assignment ${props.shiftAssignmentName}`,
			button: "Update",
			action: updateShiftAssigment,
			actionDisabled:
				form.status === shiftAssignment.value?.doc?.status &&
				form.end_date === shiftAssignment.value?.doc?.end_date,
		};
	return {
		title: "New Shift Assignment",
		button: "Submit",
		action: createShiftAssigment,
		actionDisabled: false,
	};
});

const actions = computed(() => {
	const options = [
		{
			label: `Shift for ${selectedDate.value}`,
			onClick: () => {
				deleteDialogOptions.value = {
					title: "Delete Shift?",
					message: `This will remove Shift Assignment: <a href='/app/shift-assignment/${props.shiftAssignmentName}' target='_blank'><u>${props.shiftAssignmentName}</u></a> scheduled for <b>${selectedDate.value}</b>.`,
					action: () => deleteCurrentShift.submit(),
				};
				showDeleteDialog.value = true;
			},
		},
		{
			label: "All Consecutive Shifts",
			onClick: () => {
				deleteDialogOptions.value = {
					title: "Delete Shift Assignment?",
					message: `This will delete Shift Assignment: <a href='/app/shift-assignment/${
						props.shiftAssignmentName
					}' target='_blank'><u>${
						props.shiftAssignmentName
					}</u></a> (scheduled from <b>${form.start_date}</b>${
						form.end_date ? ` to <b>${form.end_date}</b>` : ""
					}).`,
					action: async () => {
						await shiftAssignment.value.setValue.submit({ docstatus: 2 });
						shiftAssignments.delete.submit(props.shiftAssignmentName);
					},
				};
				showDeleteDialog.value = true;
			},
		},
	];
	if (form.shift_schedule_assignment)
		options.push({
			label: "Shift Schedule Assignment",
			onClick: () => {
				deleteDialogOptions.value = {
					title: "Delete Shift Schedule Assignment?",
					message: `This will delete Shift Schedule Assignment: <a href='/app/shift-schedule-assignment/${form.shift_schedule_assignment}' target='_blank'><u>${form.shift_schedule_assignment}</u></a> and all the shifts associated with it.`,
					action: () => deleteShiftScheduleAssignment.submit(),
				};
				showDeleteDialog.value = true;
			},
		});
	return options;
});

const showShiftScheduleSettings = computed(() => {
	if (!form.start_date || dayjs(form.end_date).diff(dayjs(form.start_date), "d") < 7) {
		frequency.value = "Every Week";
		return false;
	}
	return true;
});

const employees = computed(() => {
	return props.employees.map((employee) => ({
		label: `${employee.name}: ${employee.employee_name}`,
		value: employee.name,
		employee_name: employee.employee_name,
	}));
});

watch(
	() => props.isDialogOpen,
	(val) => {
		if (!val) return;

		showDeleteDialog.value = false;

		if (props.shiftAssignmentName) {
			shiftAssignment.value = getShiftAssignment(props.shiftAssignmentName);
			if (props.selectedCell) selectedDate.value = props.selectedCell.date;
		} else {
			Object.assign(form, formObject);
			if (!props.selectedCell) return;

			form.employee = { value: props.selectedCell.employee };
			form.start_date = props.selectedCell.date;
			form.end_date = props.selectedCell.date;
		}
	},
);

watch(
	() => form.employee,
	(val) => {
		if (props.shiftAssignmentName) return;
		if (val) {
			employee.fetch();
		} else {
			form.employee_name = "";
			form.company = "";
			form.department = "";
		}
	},
);

watch(
	() => form.start_date,
	() => {
		Object.assign(repeatOnDays, repeatOnDaysObject);
		if (!form.start_date) return;
		const day = dayjs(form.start_date).format("dddd");
		repeatOnDays[day as keyof typeof repeatOnDays] = true;
	},
	{ immediate: true },
);

const updateShiftAssigment = () => {
	shiftAssignment.value.setValue.submit({ status: form.status, end_date: form.end_date });
};

const createShiftAssigment = () => {
	if (
		showShiftScheduleSettings.value &&
		(Object.values(repeatOnDays).some((day) => !day) || frequency.value !== "Every Week")
	)
		createShiftAssignmentSchedule.submit();
	else insertShift.submit();
};

// RESOURCES

const getShiftAssignment = (name: string) =>
	createDocumentResource({
		doctype: "Shift Assignment",
		name: name,
		onSuccess: (data: Record<string, any>) => {
			Object.keys(form).forEach((key) => {
				form[key as keyof Form] = data[key];
			});
			if (form.shift_schedule_assignment) shiftSchedule.fetch();
		},
		onError(error: { messages: string[] }) {
			raiseToast("error", error.messages[0]);
		},
		setValue: {
			onSuccess() {
				raiseToast("success", "Shift Assignment updated successfully!");
				emit("fetchEvents");
			},
			onError(error: { messages: string[] }) {
				raiseToast("error", error.messages[0]);
			},
		},
	});

const employee = createResource({
	url: "hrms.api.roster.get_values",
	makeParams() {
		const employee = (form.employee as { value: string }).value;
		return {
			doctype: "Employee",
			name: employee,
			fields: ["employee_name", "company", "department"],
		};
	},
	onSuccess: (data: { [K in "employee_name" | "company" | "department"]: string }) => {
		form.employee_name = data.employee_name;
		form.company = data.company;
		form.department = data.department;
	},
	onError(error: { messages: string[] }) {
		raiseToast("error", error.messages[0]);
	},
});

const shiftSchedule = createResource({
	url: "hrms.api.roster.get_schedule_from_assignment",
	makeParams() {
		return { shift_schedule_assignment: form.shift_schedule_assignment };
	},
	onSuccess: (data: { frequency: string; repeat_on_days: string[] }) => {
		frequency.value = data.frequency;
		for (const day in repeatOnDays) {
			repeatOnDays[day as keyof typeof repeatOnDays] = data.repeat_on_days.includes(day);
		}
	},
	onError(error: { messages: string[] }) {
		raiseToast("error", error.messages[0]);
	},
});

const shiftAssignments = createListResource({
	doctype: "Shift Assignment",
	insert: {
		onSuccess() {
			raiseToast("success", "Shift Assignment created successfully!");
			emit("fetchEvents");
		},
		onError(error: { messages: string[] }) {
			raiseToast("error", error.messages[0]);
		},
	},
	delete: {
		onSuccess() {
			raiseToast("success", "Shift Assignment deleted successfully!");
			emit("fetchEvents");
		},
		onError(error: { messages: string[] }) {
			raiseToast("error", error.messages[0]);
		},
	},
});

const insertShift = createResource({
	url: "hrms.api.roster.insert_shift",
	makeParams() {
		return {
			employee: (form.employee as { value: string }).value,
			shift_type: form.shift_type,
			shift_location: form.shift_location,
			company: form.company,
			status: form.status,
			start_date: form.start_date,
			end_date: form.end_date,
		};
	},
	onSuccess: () => {
		raiseToast("success", "Shift Assignment created successfully!");
		emit("fetchEvents");
	},
	onError(error: { messages: string[] }) {
		raiseToast("error", error.messages[0]);
	},
});

const deleteCurrentShift = createResource({
	url: "hrms.api.roster.break_shift",
	makeParams() {
		return {
			assignment: props.shiftAssignmentName,
			date: selectedDate.value,
		};
	},
	onSuccess: () => {
		raiseToast("success", "Shift deleted successfully!");
		emit("fetchEvents");
	},
	onError(error: { messages: string[] }) {
		raiseToast("error", error.messages[0]);
	},
});

const createShiftAssignmentSchedule = createResource({
	url: "hrms.api.roster.create_shift_schedule_assignment",
	makeParams() {
		return {
			employee: (form.employee as { value: string }).value,
			shift_type: (form.shift_type as { value: string }).value,
			company: form.company,
			status: form.status,
			start_date: form.start_date,
			end_date: form.end_date,
			shift_location: (form.shift_location as { value: string }).value,
			repeat_on_days: Object.keys(repeatOnDays).filter(
				(day) => repeatOnDays[day as keyof typeof repeatOnDays],
			),
			frequency: frequency.value,
		};
	},
	onSuccess: () => {
		raiseToast("success", "Shift Schedule Assignment created successfully!");
		emit("fetchEvents");
	},
	onError(error: { messages: string[] }) {
		raiseToast("error", error.messages[0]);
	},
});

const deleteShiftScheduleAssignment = createResource({
	url: "hrms.api.roster.delete_shift_schedule_assignment",
	makeParams() {
		return { shift_schedule_assignment: form.shift_schedule_assignment };
	},
	onSuccess: () => {
		raiseToast("success", "Shift Schedule Assignment deleted successfully!");
		emit("fetchEvents");
	},
	onError(error: { messages: string[] }) {
		raiseToast("error", error.messages[0]);
	},
});
</script>
