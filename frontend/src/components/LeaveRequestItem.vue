<template>
	<div class="flex flex-col w-full justify-center gap-2.5">
		<div class="flex flex-row items-center justify-between">
			<div class="flex flex-row items-start gap-3 grow">
				<FeatherIcon name="calendar" class="h-5 w-5 text-gray-500" />
				<div class="flex flex-col items-start">
					<div class="text-lg font-normal text-gray-800">{{ props.leave.leave_type }}</div>
					<div class="text-sm font-normal text-gray-500">
						<span>{{ props.leave.leave_dates }}</span>
						<span class="whitespace-pre"> &middot; </span>
						<span class="whitespace-nowrap">{{ `${props.leave.total_leave_days}d` }}</span>
					</div>
				</div>
			</div>
			<div class="flex flex-row justify-end items-center gap-2">
				<Badge :colorMap="colorMap" :label="props.leave.status" />
				<FeatherIcon name="chevron-right" class="h-5 w-5 text-gray-500" />
			</div>
		</div>
		<div v-if="props.isTeamRequest" class="flex flex-row items-center gap-2 pl-8">
			<EmployeeAvatar :employeeID="props.leave.employee"/>
			<div class="text-sm text-gray-600 grow">{{ props.leave.employee_name }}</div>
		</div>
	</div>
</template>

<script setup>

import { FeatherIcon, Badge } from "frappe-ui"

import EmployeeAvatar from "@/components/EmployeeAvatar.vue"

const props = defineProps({
	leave: {
		type: Object,
	},
	isTeamRequest: {
		type: Boolean,
		default: false,
	}
})

const colorMap = {
	Approved: "green",
	Rejected: "red",
	Open: "yellow"
}

</script>