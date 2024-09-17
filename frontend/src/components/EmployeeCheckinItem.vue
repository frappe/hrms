<template>
	<div class="flex flex-col w-full justify-center gap-2.5">
		<div class="flex flex-row items-center justify-between">
			<div class="flex flex-row items-start gap-3 grow">
				<FeatherIcon name="clock" class="h-5 w-5 text-gray-500" />
				<div class="flex flex-col items-start gap-1.5">
					<div class="text-base font-normal text-gray-800">Log Type: {{ props.doc.log_type }}</div>
					<div class="text-xs font-normal text-gray-500">
						<span>{{ formatTimestamp(props.doc.time) }}</span>
					</div>
				</div>
			</div>
			<div class="flex flex-row justify-end items-center gap-2">
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
import { FeatherIcon } from "frappe-ui"

import EmployeeAvatar from "@/components/EmployeeAvatar.vue"
import { formatTimestamp } from "@/utils/formatters"

const props = defineProps({
	doc: {
		type: Object,
	},
})
</script>
