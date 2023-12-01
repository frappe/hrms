<template>
	<div class="flex flex-col w-full justify-center gap-2.5">
		<div class="flex flex-row items-center justify-between">
			<div class="flex flex-row items-start gap-3 grow">
				<EmployeeAdvanceIcon class="h-5 w-5 mt-[3px] text-gray-500" />
				<div class="flex flex-col items-start gap-1">
					<div
						v-if="props.doc.balance_amount"
						class="text-lg font-bold text-gray-800 leading-6"
					>
						{{ `${currency} ${props.doc.balance_amount} /` }}
						<span class="text-gray-600">
							{{ `${currency} ${props.doc.paid_amount}` }}
						</span>
					</div>
					<div v-else class="text-lg font-bold text-gray-800 leading-6">
						{{ `${currency} ${props.doc.advance_amount}` }}
					</div>
					<div class="text-xs font-normal text-gray-500">
						<span>
							{{ props.doc.purpose }}
						</span>
						<span class="whitespace-pre"> &middot; </span>
						<span class="whitespace-nowrap">
							{{ postingDate }}
						</span>
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
import { FeatherIcon, Badge } from "frappe-ui"
import { computed, inject } from "vue"

import { getCurrencySymbol } from "@/data/currencies"

import EmployeeAvatar from "@/components/EmployeeAvatar.vue"
import EmployeeAdvanceIcon from "@/components/icons/EmployeeAdvanceIcon.vue"

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

const currency = computed(() => getCurrencySymbol(props.doc.currency))

const postingDate = computed(() => {
	return dayjs(props.doc.posting_date).format("D MMM")
})

const status = computed(() => {
	return props.workflowStateField
		? props.doc[props.workflowStateField]
		: props.doc.status
})
</script>
