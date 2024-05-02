<template>
	<div class="bg-white rounded-lg border p-4">
		<!-- Header -->
		<div class="flex mb-4">
			<Button
				icon="chevron-left"
				variant="ghost"
				@click="firstOfMonth = firstOfMonth.subtract(1, 'M')"
			/>
			<span class="px-1 w-20 text-center my-auto"
				>{{ firstOfMonth.format("MMM") }} '{{ firstOfMonth.format("YY") }}</span
			>
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
						<th class="min-w-24 py-2"></th>
						<th v-for="day in daysOfMonth" :key="day" class="min-w-24 py-2">
							<div>{{ day.name }}</div>
							<div>{{ day.no }}</div>
						</th>
					</tr>
				</thead>
				<tbody>
					<tr v-for="employee in employees.data" :key="employee.name">
						<td class="min-w-24 py-2"></td>
						<td v-for="day in daysOfMonth" :key="day" class="min-w-24 py-2"></td>
					</tr>
				</tbody>
			</table>
		</div>
	</div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from "vue";
import dayjs from "../utils/dayjs";
import { createResource } from "frappe-ui";

const firstOfMonth = ref(dayjs().date(1));
watch(firstOfMonth, () => fetchShifts());

const daysOfMonth = computed(() => {
	const daysOfMonth = [];
	for (let i = 1; i <= firstOfMonth.value.daysInMonth(); i++) {
		const date = firstOfMonth.value.date(i);
		daysOfMonth.push({ no: date.format("DD"), name: date.format("ddd") });
	}
	return daysOfMonth;
});

const fetchShifts = () => {
	shifts.params = {
		filters: {
			start_date: ["<=", firstOfMonth.value.endOf("month").format("YYYY-MM-DD")],
		},
		or_filters: {
			end_date: [">=", firstOfMonth.value.format("YYYY-MM-DD")],
			end_date: ["is", "not set"],
		},
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
	onSuccess: (data) => {
		console.log(data);
	},
});
fetchShifts();
</script>
