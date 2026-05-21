<template>
	<ListItem
		:isTeamRequest="props.isTeamRequest"
		:employee="props.doc.employee"
		:employeeName="props.doc.employee_name"
	>
		<template #left>
			<TimesheetIcon class="h-5 w-5 text-gray-500" />
			<div class="flex flex-col items-start gap-1.5">
				<div class="text-base font-normal text-gray-800">
					{{ props.doc.name }}
				</div>
				<div class="text-xs font-normal text-gray-500">
					<span>{{ dateRange }}</span>
					<span v-if="props.doc.total_hours" class="whitespace-pre"> &middot; </span>
					<span v-if="props.doc.total_hours" class="whitespace-nowrap">
						{{ props.doc.total_hours }} hrs
					</span>
				</div>
			</div>
		</template>
		<template #right>
			<Badge
				variant="outline"
				:theme="statusMap[status]"
				:label="__(status, null, 'Timesheet')"
				size="md"
			/>
			<FeatherIcon name="chevron-right" class="h-5 w-5 text-gray-500" />
		</template>
	</ListItem>
</template>

<script setup>
import { computed, inject } from "vue"
import { FeatherIcon, Badge } from "frappe-ui"

import ListItem from "@/components/ListItem.vue"
import TimesheetIcon from "@/components/icons/TimesheetIcon.vue"

const dayjs = inject("$dayjs")
const __ = inject("$translate")

const props = defineProps({
	doc: { type: Object },
	isTeamRequest: { type: Boolean, default: false },
	workflowStateField: { type: String, required: false },
})

const statusMap = {
	Draft: "gray",
	Submitted: "blue",
	Cancelled: "red",
}

const status = computed(() => {
	if (props.workflowStateField) return props.doc[props.workflowStateField]
	return props.doc.status || "Draft"
})

const dateRange = computed(() => {
	if (!props.doc.start_date) return ""
	if (!props.doc.end_date || props.doc.start_date === props.doc.end_date) {
		return dayjs(props.doc.start_date).format("D MMM YYYY")
	}
	return `${dayjs(props.doc.start_date).format("D MMM")} – ${dayjs(props.doc.end_date).format("D MMM YYYY")}`
})
</script>
