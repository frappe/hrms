<template>
	<div class="flex flex-col w-full justify-center gap-2.5">
		<div class="flex flex-row items-center justify-between">
			<div class="flex flex-row items-start gap-3 grow">
				<AttendanceIcon class="h-5 w-5 text-gray-500" />
				<div class="flex flex-col items-start gap-1.5">
					<div class="text-base font-normal text-gray-800">
						{{ props.doc.reason }}
					</div>
					<div class="text-xs font-normal text-gray-500">
						<span>{{ props.doc.leave_dates || getLeaveDates(props.doc) }}</span>
						<span class="whitespace-pre"> &middot; </span>
					</div>
				</div>
			</div>
			<div class="flex flex-row justify-end items-center gap-2">
				<FeatherIcon name="chevron-right" class="h-5 w-5 text-gray-500" />
			</div>
		</div>
	</div>
</template>

<script setup>
import { FeatherIcon} from "frappe-ui"
import AttendanceIcon from "@/components/icons/AttendanceIcon.vue"
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
</script>
