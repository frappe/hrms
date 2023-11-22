<template>
	<div class="flex flex-col w-full">
		<div class="flex flex-row justify-between items-center px-4">
			<div class="text-lg text-gray-800 font-bold">Leave Balance</div>
			<router-link
				:to="{ name: 'LeaveApplicationListView' }"
				v-slot="{ navigate }"
				v-if="leaveBalance.data"
			>
				<div
					@click="navigate"
					class="text-sm text-gray-800 font-semibold cursor-pointer underline underline-offset-2"
				>
					View Leave History
				</div>
			</router-link>
		</div>

		<!-- Leave Balance Dashboard -->
		<div
			class="flex flex-row gap-4 overflow-x-auto py-2 mt-3"
			v-if="leaveBalance.data"
		>
			<div
				v-for="(allocation, leave_type, index) in leaveBalance.data"
				:key="leave_type"
				class="flex flex-col bg-white border-none rounded-lg drop-shadow-md gap-2 p-4 items-start first:ml-4"
			>
				<SemicircleChart
					:percentage="allocation.balance_percentage"
					:colorClass="getChartColor(index)"
				/>
				<div class="text-gray-800 font-bold text-base">
					{{ `${allocation.balance_leaves}/${allocation.allocated_leaves}` }}
				</div>
				<div class="text-gray-600 font-normal text-sm w-24 leading-4">
					{{ `${leave_type} balance` }}
				</div>
			</div>
		</div>

		<EmptyState message="You have no leaves allocated" v-else />
	</div>
</template>

<script setup>
import { inject, onMounted, onBeforeUnmount } from "vue"
import { createResource } from "frappe-ui"

import SemicircleChart from "@/components/SemicircleChart.vue"

const employee = inject("$employee")
const socket = inject("$socket")

const leaveBalance = createResource({
	url: "hrms.api.get_leave_balance_map",
	params: {
		employee: employee.data.name,
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
	// note: tw colors - rose-400, pink-400 & purple-500 of the old frappeui palette #918ef5
	const chartColors = ["text-[#fb7185]", "text-[#f472b6]", "text-[#918ef5]"]
	return chartColors[index % chartColors.length]
}

onMounted(() => {
	socket.on("hrms:update_leaves", (data) => {
		if (data.employee === employee.data.name) {
			leaveBalance.reload()
		}
	})
})

onBeforeUnmount(() => {
	socket.off("hrms:update_leaves")
})
</script>
