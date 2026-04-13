<template>
	<ListItem
		:isTeamRequest="props.isTeamRequest"
		:employee="props.doc.raised_by"
		:employeeName="props.doc.raised_by_name"
	>
		<template #left>
			<GrievanceIcon class="h-5 w-5 text-gray-500" />
			<div class="flex flex-col items-start gap-1.5">
				<div class="text-base font-normal text-gray-800">
					{{ props.doc.subject }}
				</div>
				<div class="text-xs font-normal text-gray-500">
					{{ dayjs(props.doc.date).format("D MMM YYYY") }}
				</div>
			</div>
		</template>
		<template #right>
			<Badge
				variant="outline"
				:theme="statusMap[props.doc.status]"
				:label="__(props.doc.status, null, 'Employee Grievance')"
				size="md"
			/>
			<FeatherIcon name="chevron-right" class="h-5 w-5 text-gray-500" />
		</template>
	</ListItem>
</template>

<script setup>
import { FeatherIcon, Badge } from "frappe-ui"
import { inject } from "vue"

import ListItem from "@/components/ListItem.vue"
import GrievanceIcon from "@/components/icons/GrievanceIcon.vue"

const dayjs = inject("$dayjs")
const __ = inject("$translate")

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

const statusMap = {
	Open: "orange",
	Resolved: "green",
	Invalid: "red",
}
</script>
