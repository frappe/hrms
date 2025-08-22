<template>
	<div class="flex flex-col w-full">
		<div class="flex flex-row justify-between items-center px-4">
			<div class="text-lg text-gray-800 font-bold">{{ __("Leave Balance") }} </div>
			<router-link
				:to="{ name: 'LeaveApplicationListView' }"
				v-slot="{ navigate }"
				v-if="leaveBalance.data"
			>
				<div
					@click="navigate"
					class="text-sm text-gray-800 font-semibold cursor-pointer underline underline-offset-2"
				>
					{{ __("View Leave History") }}
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
					{{ __("{0} balance", [__(leave_type, null, "Leave Type")]) }}
				</div>
			</div>
		</div>

		<EmptyState :message="__('You have no leaves allocated')" v-else />
	</div>
</template>

<script setup>
import SemicircleChart from "@/components/SemicircleChart.vue"
import { leaveBalance } from "@/data/leaves"
import { inject } from "vue"

const __ = inject("$translate")
const getChartColor = (index) => {
	// note: tw colors - rose-400, pink-400 & purple-500 of the old frappeui palette #918ef5
	const chartColors = ["text-[#fb7185]", "text-[#f472b6]", "text-[#918ef5]"]
	return chartColors[index % chartColors.length]
}
</script>
