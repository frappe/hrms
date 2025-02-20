<script setup lang="ts">
import { onMounted, computed, watch, ref } from "vue";
import MonthlyReal from "./components/MonthlyReal.vue";

const provisionalId = computed(() => {
	const route = frappe.get_route();
	if (route.length > 1) {
		return route[1];
	}
	return null;
});
const provisionalData = ref(null);

const startDate = ref(null);
const employees = ref([]);
const shifts = ref([]);
const reals = ref([]);
const startOfMonth = computed(() => {
	return new Date(startDate.value.getFullYear(), startDate.value.getMonth(), 1);
});
const numberOfDaysInMonth = computed(() => {
	return new Date(startDate.value.getFullYear(), startDate.value.getMonth() + 1, 0).getDate();
});
const endOfMonth = computed(() => {
	return new Date(startDate.value.getFullYear(), startDate.value.getMonth() + 1);
});

onMounted(() => {
	frappe.breadcrumbs.clear();
	frappe.breadcrumbs.append_breadcrumb_element("/app/roster", "Provisional Plans");

	frappe.db.get_doc("Provisional Plan", provisionalId.value).then((doc) => {
		provisionalData.value = doc;
		startDate.value = new Date(doc.start_date);
		shifts.value = JSON.parse(doc.shifts);
		employees.value = Array(doc.employees.length).fill(0);

		const rshifts = Array(doc.employees.length)
			.fill(0)
			.map((_, i) => {
				return Array(numberOfDaysInMonth.value).fill([]);
			});

		frappe.db
			.get_list("Employee", {
				limit: 0,
				filters: [["name", "in", doc.employees.map((e) => e.employee)]],
				fields: ["*"],
			})
			.then((res) => {
				const map = res.reduce((acc, cur) => {
					acc[cur.name] = cur;
					return acc;
				}, {});
				employees.value = doc.employees.map((e) => {
					return map[e.employee];
				});
			});

		Promise.all([
			frappe.db
				.get_list("Leave Allocation", {
					limit: 0,
					filters: [
						["employee", "in", doc.employees.map((e) => e.employee)],
						["from_date", ">=", startOfMonth.value.toISOString().split("T")[0]],
						["to_date", "<=", endOfMonth.value.toISOString().split("T")[0]],
						["docstatus", "=", 1],
					],
					fields: ["*"],
				})
				.then((res) => {
					console.log("leave allocation", res);
					for (let r of res) {
						const dateIndex = new Date(r.from_date).getDate() - 1;
						const employeeIndex = doc.employees.findIndex(
							(e) => e.employee === r.employee
						);

						const from_date = new Date(r.from_date);
						const to_date = new Date(r.to_date);
						const diff = to_date.getDate() - from_date.getDate();
						r.type = "L";
						if (diff > 1) {
							for (let i = 0; i <= diff; i++) {
								rshifts[employeeIndex][dateIndex + i] = [
									...rshifts[employeeIndex][dateIndex + i],
									r,
								];
							}
						} else {
							rshifts[employeeIndex][dateIndex] = [
								...rshifts[employeeIndex][dateIndex],
								r,
							];
						}
					}
					// reals.value = rshifts;
				}),
			frappe.db
				.get_list("Shift Assignment", {
					limit: 0,
					filters: [
						["department", "=", provisionalData.value.department],
						["start_date", ">=", startOfMonth.value.toISOString().split("T")[0]],
						["start_date", "<=", endOfMonth.value.toISOString().split("T")[0]],
					],
					fields: ["*"],
				})
				.then((res) => {
					for (let r of res) {
						const dateIndex = new Date(r.start_date).getDate() - 1;
						const employeeIndex = doc.employees.findIndex(
							(e) => e.employee === r.employee
						);
						r.type = r.shift_type;
						rshifts[employeeIndex][dateIndex] = [
							...rshifts[employeeIndex][dateIndex],
							r,
						];
					}

					console.log("rshifts", rshifts);
				}),
		]).then(() => {
			console.log("done");
			reals.value = rshifts;
		});
	});
});

const assignRealShift = () => {
	frappe.call({
		method: "hrms.hr.doctype.provisional_plan.provisional_plan.create_shifts",
		args: {
			provisional_plan: provisionalId.value,
		},
		callback: function (r) {
			console.log(r);
		},
	});
};

const deleteProvisionalPlan = () => {
	frappe.confirm(__("Are you sure you want to delete the provisional plan"), () => {
		frappe.db.delete_doc("Provisional Plan", provisionalId.value).then(() => {
			frappe.set_route(["roster"]);
		});
	});
};
</script>
<template>
	<div>
		<h3>{{ provisionalId }}</h3>
		<div class="float-right">
			<button class="btn btn-danger mr-2" @click="deleteProvisionalPlan">Delete</button>
			<button
				v-if="provisionalData"
				class="btn btn-primary"
				:disabled="provisionalData.real_shift_assigned"
				@click="assignRealShift"
			>
				Assign Real Shift
			</button>
			<a class="btn btn-info ml-2" href="/hr/roster" target="_blank"> Show Real Shifts </a>
		</div>
		<div class="w-25">
			<table v-if="provisionalData" class="table">
				<tbody>
					<tr>
						<th scope="row">Title</th>
						<td>{{ provisionalData.title }}</td>
					</tr>
					<tr>
						<th scope="row">Month</th>
						<td>{{ provisionalData.month + " " + provisionalData.year }}</td>
					</tr>
					<tr>
						<th scope="row">Department</th>
						<td>{{ provisionalData.department }}</td>
					</tr>
					<tr>
						<th scope="row">Index</th>
						<td>{{ provisionalData.start_date }}</td>
					</tr>
				</tbody>
			</table>
		</div>

		<MonthlyReal
			v-if="provisionalData"
			:shifts="shifts"
			:reals="reals"
			:department="provisionalData.department"
			:employees="employees"
			:startDate="startDate"
		/>
	</div>
</template>
