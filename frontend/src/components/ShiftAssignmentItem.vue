<template>
	<div class="flex flex-col w-full justify-center gap-2.5">
		<div class="flex flex-row items-center justify-between">
			<div class="flex flex-row items-start gap-3 grow">
				<FeatherIcon name="clock" class="h-5 w-5 text-gray-500" />
				<div class="flex flex-col items-start gap-1.5">
					<div class="text-base font-normal text-gray-800">
						{{ props.doc.shift_type }}
					</div>
					<div class="text-xs font-normal text-gray-500">
						<span>{{ props.doc.shift_dates || getShiftDates(props.doc) }}</span>
						<span v-if="props.doc.end_date" class="whitespace-pre"> &middot; </span>
						<span v-if="props.doc.end_date" class="whitespace-nowrap">{{
							`${props.doc.total_shift_days || getTotalShiftDays(props.doc)}d`
						}}</span>
					</div>
				</div>
			</div>
			<div class="flex flex-row justify-end items-center gap-2">
				<span v-if="props.doc.shift_timing" class="text-gray-700 font-normal rounded text-base">
					{{ props.doc.shift_timing }}
				</span>
				<Badge v-else variant="outline" :theme="colorMap[status]" :label="status" size="md" />
				<FeatherIcon name="chevron-right" class="h-5 w-5 text-gray-500" />
			</div>
		</div>
		<div v-if="props.isTeamRequest" class="flex flex-row items-center gap-2 pl-8">
			<EmployeeAvatar :employeeID="props.doc.employee" />
			<div class="text-sm text-gray-600 grow">
				{{ props.doc.employee_name }}
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue"
import { Badge, FeatherIcon } from "frappe-ui"

import EmployeeAvatar from "@/components/EmployeeAvatar.vue"
import { getShiftDates, getTotalShiftDays } from "@/data/attendance"

const props = defineProps({
	doc: {
		type: Object,
	},
})

const status = computed(() => {
	if (props.workflowStateField) return props.doc[props.workflowStateField]
	return props.doc.docstatus ? "Submitted" : "Draft"
})

const colorMap = {
	Submitted: "blue",
	Draft: "gray",
}
</script>
