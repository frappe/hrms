<template>
	<div class="flex flex-col w-full justify-center gap-2.5">
		<div class="flex flex-row items-center justify-between">
			<div class="flex flex-row items-start gap-3 grow">
				<LeaveIcon class="h-5 w-5 text-gray-500" />
				<div class="flex flex-col items-start gap-1.5">
					<div class="text-base font-normal text-gray-800">
						{{ props.doc.leave_type }}
					</div>
					<div class="text-xs font-normal text-gray-500">
						<span>{{ props.doc.leave_dates || getLeaveDates(props.doc) }}</span>
						<span class="whitespace-pre"> &middot; </span>
						<span class="whitespace-nowrap">{{
							`${props.doc.total_leave_days}d`
						}}</span>
					</div>
				</div>
			</div>
			<div class="flex flex-row justify-end items-center gap-2">
				<Badge
					variant="outline"
					:theme="colorMap[status]"
					:label="status"
					size="md"
				/>
				<FeatherIcon name="chevron-right" class="h-5 w-5 text-gray-500" />
			</div>
		</div>
		<div
			v-if="props.isTeamRequest"
			class="flex flex-row items-center gap-2 pl-8"
		>
			<EmployeeAvatar :employeeID="props.doc.employee" />
			<div class="text-sm text-gray-600 grow">
				{{ props.doc.employee_name }}
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue"
import { FeatherIcon, Badge } from "frappe-ui"

import EmployeeAvatar from "@/components/EmployeeAvatar.vue"
import LeaveIcon from "@/components/icons/LeaveIcon.vue"
import { getLeaveDates } from "@/data/leaves"

const props = defineProps({
	doc: {
		type: Object,
	},
	isTeamRequest: {
		type: Boolean,
		default: false,
	},
	workflowStateField: {
		type: String,
		required: false,
	},
})

const status = computed(() => {
	return props.workflowStateField
		? props.doc[props.workflowStateField]
		: props.doc.status
})

const colorMap = {
	Approved: "green",
	Rejected: "red",
	Open: "orange",
}
</script>
