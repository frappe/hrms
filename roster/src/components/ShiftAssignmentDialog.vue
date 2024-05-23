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
			</div>
		</template>
		<template #actions>
			<div class="flex space-x-2 justify-end">
				<Dropdown
					v-if="props.shiftAssignmentName"
					:options="[
						{
							label: 'Delete Assignment',
							icon: 'trash',
							onClick: async () => {
								await shiftAssignment.setValue.submit({ docstatus: 2 });
								shiftAssignments.delete.submit(props.shiftAssignmentName);
							},
						},
					]"
				>
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

type Status = "Active" | "Inactive";

type Form = {
	[K in
		| "company"
		| "employee_name"
		| "start_date"
		| "end_date"
		| "department"
		| "employee"
		| "shift_type"]: string | { value: string; label?: string };
} & {
	status: Status | { value: Status; label?: Status };
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

const defaultForm: Form = {
	employee: "",
	company: "",
	employee_name: "",
	start_date: "",
	shift_type: "",
	end_date: "",
	status: "Active",
	department: "",
};

const form = reactive({ ...defaultForm });
const shiftAssignment = ref();

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
			Object.assign(form, defaultForm);
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

const updateShiftAssigment = () => {
	shiftAssignment.value.setValue.submit({ status: form.status, end_date: form.end_date });
};

const createShiftAssigment = () => {
	const employee = (form.employee as { value: string }).value;
	const shiftType = (form.shift_type as { value: string }).value;

	shiftAssignments.insert.submit({
		...form,
		employee: employee,
		shift_type: shiftType,
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
		setValue: {
			onSuccess() {
				emit("fetchEvents");
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
});

const shiftTypes = createListResource({
	doctype: "Shift Type",
	fields: ["name"],
	transform: (data: { name: string }[]) => data.map((shiftType) => shiftType.name),
	auto: true,
});

const shiftAssignments = createListResource({
	doctype: "Shift Assignment",
	insert: {
		onSuccess() {
			emit("fetchEvents");
		},
	},
	delete: {
		onSuccess() {
			emit("fetchEvents");
		},
	},
});
</script>
