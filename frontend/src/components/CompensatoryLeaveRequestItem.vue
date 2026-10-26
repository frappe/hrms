<template>
	<ListItem
		:isTeamRequest="props.isTeamRequest"
		:employee="props.doc.employee"
		:employeeName="props.doc.employee_name"
	>
		<template #left>
			<LeaveIcon class="h-5 w-5 text-gray-500" />
			<div class="flex flex-col items-start gap-1.5">
				<div class="text-base font-normal text-gray-800">
					{{ __(props.doc.leave_type, null, "Leave Type") }}
				</div>
				<div class="text-xs font-normal text-gray-500">
					<span>{{ workDates }}</span>
					<span class="whitespace-pre"> &middot; </span>
					<span class="whitespace-nowrap">{{ __("{0}d", [totalDays]) }}</span>
				</div>
			</div>
		</template>
		<template #right>
			<Badge variant="outline" :theme="colorMap[status] || 'gray'" :label="__(status)" size="md" />
			<FeatherIcon name="chevron-right" class="h-5 w-5 text-gray-500" />
		</template>
	</ListItem>
</template>

<script setup>
import { computed, inject } from "vue"
import { Badge, FeatherIcon } from "frappe-ui"
import ListItem from "@/components/ListItem.vue"
import LeaveIcon from "@/components/icons/LeaveIcon.vue"

const props = defineProps({
	doc: { type: Object, required: true },
	isTeamRequest: { type: Boolean, default: false },
	workflowStateField: String,
})
const dayjs = inject("$dayjs")
const __ = inject("$translate")
const workDates = computed(() => {
	const from = dayjs(props.doc.work_from_date).format("D MMM")
	return props.doc.work_from_date === props.doc.work_end_date
		? from
		: `${from} - ${dayjs(props.doc.work_end_date).format("D MMM")}`
})
const totalDays = computed(
	() =>
		dayjs(props.doc.work_end_date).diff(dayjs(props.doc.work_from_date), "day") +
		1 -
		(props.doc.half_day ? 0.5 : 0)
)
const status = computed(() =>
	props.workflowStateField
		? props.doc[props.workflowStateField]
		: ["Draft", "Submitted", "Cancelled"][props.doc.docstatus]
)
const colorMap = { Draft: "gray", Submitted: "blue", Cancelled: "red" }
</script>
