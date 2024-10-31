<template>
	<ListItem
		:isTeamRequest="props.isTeamRequest"
		:employee="props.doc.employee"
		:employeeName="props.doc.employee_name"
	>
		<template #left>
			<EmployeeAdvanceIcon class="h-5 w-5 mt-[3px] text-gray-500" />
			<div class="flex flex-col items-start gap-1">
				<div v-if="props.doc.balance_amount" class="text-lg font-bold text-gray-800 leading-6">
					{{ formatCurrency(props.doc.balance_amount, props.doc.currency) }}
					/
					<span class="text-gray-600">
						{{ formatCurrency(props.doc.paid_amount, props.doc.currency) }}
					</span>
				</div>
				<div v-else class="text-lg font-bold text-gray-800 leading-6">
					{{ formatCurrency(props.doc.advance_amount, props.doc.currency) }}
				</div>
				<div class="text-xs font-normal text-gray-500">
					<span>
						{{ __(props.doc.purpose) }}
					</span>
					<span class="whitespace-pre"> &middot; </span>
					<span class="whitespace-nowrap">
						{{ postingDate }}
					</span>
				</div>
			</div>
		</template>
		<template #right>
			<Badge variant="outline" :theme="colorMap[status]" :label="__(status, null, 'Employee Advance')" size="md" />
			<FeatherIcon name="chevron-right" class="h-5 w-5 text-gray-500" />
		</template>
	</ListItem>
</template>

<script setup>
import { FeatherIcon, Badge } from "frappe-ui"
import { computed, inject } from "vue"

import ListItem from "@/components/ListItem.vue"
import EmployeeAdvanceIcon from "@/components/icons/EmployeeAdvanceIcon.vue"
import { formatCurrency } from "@/utils/formatters"

const dayjs = inject("$dayjs")
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

const colorMap = {
	Paid: "green",
	Unpaid: "orange",
	Claimed: "blue",
	Returned: "gray",
	"Partly Claimed and Returned": "orange",
}

const postingDate = computed(() => {
	return dayjs(props.doc.posting_date).format("D MMM")
})

const status = computed(() => {
	return props.workflowStateField ? props.doc[props.workflowStateField] : props.doc.status
})
</script>
