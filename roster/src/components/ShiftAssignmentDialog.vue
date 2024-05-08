<template>
	<Dialog :options="{ title: dialog.title, size: '4xl' }">
		<template #body-content>
			<div class="grid grid-cols-2 gap-6">
				<Autocomplete
					type="text"
					label="Employee"
					v-model="form.employee"
					:class="!!props.shiftAssignmentName && 'pointer-events-none'"
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
				<Autocomplete
					type="text"
					label="Employee"
					v-model="form.shift_type"
					:class="!!props.shiftAssignmentName && 'pointer-events-none'"
					:options="shiftTypes.data"
				/>
				<FormControl id="end_date" type="date" label="End Date" v-model="form.end_date" />
				<FormControl
					id="staus"
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
			<div class="flex">
				<Button class="ml-auto" @click="emit('closeDialog')"> Close </Button>
				<Button variant="solid" class="ml-2" @click="dialog.action">
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
	Autocomplete,
	FormControl,
	createDocumentResource,
	createResource,
	createListResource,
} from "frappe-ui";

const props = defineProps({
	shiftAssignmentName: {
		type: String,
		required: false,
	},
	selectedCell: {
		type: Object,
		required: true,
	},
	employees: {
		type: Array,
		required: false,
		default: [],
	},
});

const emit = defineEmits(["fetchShifts", "closeDialog"]);

const defaultForm = {
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
		};
	return {
		title: "New Shift Assignment",
		button: "Submit",
		action: createShiftAssigment,
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
	() => props.selectedCell,
	(val) => {
		if (props.shiftAssignmentName || !val.employee) return;
		form.employee = { value: val.employee };
		form.start_date = val.date;
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
	shiftAssignments.insert.submit({
		...form,
		employee: form.employee.value,
		shift_type: form.shift_type.value,
		docstatus: 1,
	});
};

// RESOURCES

const getShiftAssignment = (name) =>
	createDocumentResource({
		doctype: "Shift Assignment",
		name: name,
		onSuccess: (data) => {
			Object.keys(form).forEach((key) => {
				form[key] = data[key];
			});
		},
		setValue: {
			onSuccess() {
				emit("fetchShifts");
				emit("closeDialog");
			},
		},
	});

const employee = createResource({
	url: "hrms.api.roster.get_values",
	makeParams() {
		return {
			doctype: "Employee",
			name: form.employee.value,
			fields: ["employee_name", "company", "department"],
		};
	},
	onSuccess: (data) => {
		form.employee_name = data.employee_name;
		form.company = data.company;
		form.department = data.department;
	},
});

const shiftTypes = createListResource({
	doctype: "Shift Type",
	fields: ["name"],
	transform: (data) => data.map((shiftType) => shiftType.name),
	auto: true,
});

const shiftAssignments = createListResource({
	doctype: "Shift Assignment",
	insert: {
		onSuccess() {
			emit("fetchShifts");
			emit("closeDialog");
		},
	},
});
</script>
