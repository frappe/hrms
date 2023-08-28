<template>
	<div class="flex flex-col w-full mt-7">
		<div class="flex flex-row justify-between items-center px-4">
			<div class="text-xl text-gray-800 font-bold">Leave Balance</div>
			<div
				class="text-lg text-blue-500 font-medium cursor-pointer"
				v-if="leaveBalance.data"
			>
				<router-link
					:to="{ name: 'LeaveApplicationListView' }"
					v-slot="{ navigate }"
					v-if="leaveBalance.data"
				>
					<div
						@click="navigate"
						class="text-lg text-blue-500 font-medium cursor-pointer"
					>
						View Leave History
					</div>
				</router-link>
			</div>
		</div>

		<!-- Leave Balance Dashboard -->
		<div
			class="flex flex-row gap-4 overflow-x-auto py-2 mt-3"
			v-if="leaveBalance.data"
		>
			<div
				v-for="(allocation, leave_type, index) in leaveBalance.data"
				:key="leave_type"
				class="flex flex-col bg-white rounded-xl shadow-md gap-2 p-4 items-start first:ml-4"
			>
				<SemicircleChart
					:percentage="allocation.balance_percentage"
					:colorClass="getChartColor(index)"
				/>
				<div class="text-gray-800 font-bold text-lg">
					{{ `${allocation.balance_leaves}/${allocation.allocated_leaves}` }}
				</div>
				<div class="text-gray-600 font-normal text-base w-24">
					{{ `${leave_type} balance` }}
				</div>
			</div>
		</div>

		<EmptyState message="You have no leaves allocated" v-else />
	</div>
</template>

<script setup>
import { inject } from "vue"
import { createResource } from "frappe-ui"

import SemicircleChart from "@/components/SemicircleChart.vue"

const employee = inject("$employee")

const leaveBalance = createResource({
	url: "hrms.api.get_leave_balance_map",
	params: {
		employee: employee().name,
	},
	auto: true,
	transform: (data) => {
		// Calculate balance percentage for each leave type
		return Object.fromEntries(
			Object.entries(data).map(([leave_type, allocation]) => {
				allocation.balance_percentage =
					(allocation.balance_leaves / allocation.allocated_leaves) * 100
				return [leave_type, allocation]
			})
		)
	},
})

const getChartColor = (index) => {
	const chartColors = ["text-pink-500", "text-orange-400", "text-purple-500"]
	return chartColors[index % chartColors.length]
}
</script>
