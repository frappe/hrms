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
					type="date"
					label="Start Date"
					v-model="form.start_date"
					:disabled="!!props.shiftAssignmentName"
				/>
				<FormControl
					type="autocomplete"
					label="Shift Type"
					v-model="form.shift_type"
					:disabled="!!props.shiftAssignmentName"
					:options="shiftTypes.data"
				/>
				<FormControl type="date" label="End Date" v-model="form.end_date" />
				<FormControl
					type="select"
					:options="['Active', 'Inactive']"
					label="Status"
					v-model="form.status"
				/>
				<FormControl
					type="text"
					label="Department"
					v-model="form.department"
					:disabled="true"
				/>
				<div v-if="!props.shiftAssignmentName">
					<FormControl
						type="checkbox"
						label="Select Working Days"
						v-model="selectDays"
						:disabled="differenceBetweenDates <= 7"
					/>
				</div>
				<div v-if="!props.shiftAssignmentName" />
				<div v-if="!props.shiftAssignmentName && selectDays" class="space-y-1.5">
					<div class="text-xs text-gray-600">Days</div>
					<div
						class="border rounded grid grid-flow-col h-7 justify-stretch overflow-clip"
					>
						<div
							v-for="(isSelected, day) of workingDays"
							class="cursor-pointer flex flex-col"
							:class="{
								'border-r': day !== 'Sunday',
								'bg-gray-100 text-gray-500': !isSelected,
							}"
							@click="workingDays[day] = !workingDays[day]"
						>
							<div class="text-center text-sm my-auto">
								{{ day.substring(0, 3) }}
							</div>
						</div>
					</div>
				</div>
				<FormControl
					v-if="!props.shiftAssignmentName && selectDays"
					type="select"
					:options="['Every Week', 'Every 2 Weeks', 'Every 3 Weeks', 'Every 4 Weeks']"
					label="Frequency"
					v-model="frequency"
				/>
			</div>
		</template>
		<template #actions>
			<div class="flex space-x-2 justify-end">
				<Dropdown v-if="props.shiftAssignmentName" :options="actions">
					<Button size="md" icon="more-vertical" />
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
	Dialog,
	FormControl,
	Dropdown,
	createDocumentResource,
	createResource,
	createListResource,
} from "frappe-ui";

import { dayjs, raiseToast } from "../utils";

type Status = "Active" | "Inactive";

type Form = {
	[K in "company" | "employee_name" | "department" | "employee" | "shift_type"]:
		| string
		| { value: string; label?: string };
} & {
	start_date: string;
	end_date: string;
	status: Status | { value: Status; label?: Status };
	group?: string;
};

interface Props {
	isDialogOpen: boolean;
	shiftAssignmentName?: string;
	selectedCell: {
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
	start_date: "",
	shift_type: "",
	end_date: "",
	status: "Active",
	department: "",
	group: "",
};

const workingDaysObject = {
	Monday: false,
	Tuesday: false,
	Wednesday: false,
	Thursday: false,
	Friday: false,
	Saturday: false,
	Sunday: false,
};

const form = reactive({ ...formObject });
const workingDays = reactive({ ...workingDaysObject });

const shiftAssignment = ref();
const selectDays = ref(false);
const frequency = ref("Every Week");

const dialog = computed(() => {
	if (props.shiftAssignmentName)
		return {
			title: `Shift Assignment ${props.shiftAssignmentName}`,
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
			label: "Delete Current Shift",
			icon: "trash",
			onClick: async () => {
				await shiftAssignment.value.setValue.submit({ docstatus: 2 });
				shiftAssignments.delete.submit(props.shiftAssignmentName);
			},
		},
	];
	if (form.group)
		options.push({
			label: "Delete Shift Group",
			icon: "trash",
			onClick: async () => {
				deleteRepeatingShiftAssignment.submit(form.group);
			},
		});
	return options;
});

const differenceBetweenDates = computed(() => {
	let difference = 0;
	if (form.start_date && form.end_date)
		difference = dayjs(form.end_date).diff(dayjs(form.start_date), "d");
	if (difference <= 7) selectDays.value = false;
	return difference;
});

const employees = computed(() => {
	return props.employees.map((employee) => ({
		label: `${employee.name}: ${employee.employee_name}`,
		value: employee.name,
		employee_name: employee.employee_name,
	}));
});

watch(
	() => props.shiftAssignmentName,
	(val) => {
		if (val) shiftAssignment.value = getShiftAssignment(val);
		else {
			Object.assign(form, formObject);
			form.employee = { value: props.selectedCell.employee };
			form.start_date = props.selectedCell.date;
		}
	},
);

watch(
	() => props.isDialogOpen,
	(val) => {
		if (val && !props.shiftAssignmentName) {
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
		selectDefaultWorkingDay();
	},
);

watch(selectDays, (val) => {
	if (!val) {
		selectDefaultWorkingDay();
		frequency.value = "Every Week";
	}
});

const selectDefaultWorkingDay = () => {
	Object.assign(workingDays, workingDaysObject);
	if (form.start_date) {
		const day = dayjs(form.start_date).format("dddd");
		workingDays[day as keyof typeof workingDays] = true;
	}
};

const updateShiftAssigment = () => {
	shiftAssignment.value.setValue.submit({ status: form.status, end_date: form.end_date });
};

const createShiftAssigment = () => {
	if (selectDays.value) createRepeatingShiftAssignment.submit();
	else
		shiftAssignments.insert.submit({
			...form,
			employee: (form.employee as { value: string }).value,
			shift_type: (form.shift_type as { value: string }).value,
			docstatus: 1,
		});
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

const shiftTypes = createListResource({
	doctype: "Shift Type",
	fields: ["name"],
	auto: true,
	transform: (data: { name: string }[]) => data.map((shiftType) => shiftType.name),
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

const createRepeatingShiftAssignment = createResource({
	url: "hrms.api.roster.create_repeating_shift_assignment",
	makeParams() {
		return {
			employee: (form.employee as { value: string }).value,
			shift_type: (form.shift_type as { value: string }).value,
			company: form.company,
			status: form.status,
			start_date: form.start_date,
			end_date: form.end_date,
			days: Object.keys(workingDays).filter(
				(day) => workingDays[day as keyof typeof workingDays],
			),
			frequency: frequency.value,
		};
	},
	onSuccess: () => {
		raiseToast("success", "Shift Assignment Group created successfully!");
		emit("fetchEvents");
	},
	onError(error: { messages: string[] }) {
		raiseToast("error", error.messages[0]);
	},
});

const deleteRepeatingShiftAssignment = createResource({
	url: "hrms.api.roster.delete_repeating_shift_assignment",
	makeParams() {
		return { group: form.group };
	},
	onSuccess: () => {
		raiseToast("success", "Shift Assignment Group deleted successfully!");
		emit("fetchEvents");
	},
	onError(error: { messages: string[] }) {
		raiseToast("error", error.messages[0]);
	},
});
</script>
