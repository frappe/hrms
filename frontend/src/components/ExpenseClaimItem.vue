<template>
	<div class="flex flex-col w-full justify-center gap-2.5">
		<div class="flex flex-row items-center justify-between">
			<div class="flex flex-row items-start gap-3 grow">
				<ExpenseIcon class="h-5 w-5 text-gray-500" />
				<div class="flex flex-col items-start gap-1.5">
					<div class="text-base font-normal text-gray-800">
						{{ claimTitle }}
					</div>
					<div class="text-xs font-normal text-gray-500">
						<span>
							{{ `${currency} ${props.doc.total_claimed_amount}` }}
						</span>
						<span class="whitespace-pre"> &middot; </span>
						<span class="whitespace-nowrap">
							{{ claimDates }}
						</span>
					</div>
				</div>
			</div>
			<div class="flex flex-row justify-end items-center gap-2">
				<Badge
					variant="outline"
					:theme="statusMap[props.doc.status]"
					:label="props.doc.status"
					size="sm"
				/>
				<Badge
					:theme="approvalStatusMap[props.doc.approval_status]"
					:label="approvalStatus"
					size="sm"
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

import EmployeeAvatar from "@/components/EmployeeAvatar.vue"
import ExpenseIcon from "@/components/icons/ExpenseIcon.vue"

import { getCompanyCurrencySymbol } from "@/data/currencies"

const dayjs = inject("$dayjs")
const props = defineProps({
	doc: {
		type: Object,
	},
	isTeamRequest: {
		type: Boolean,
		default: false,
	},
})

const statusMap = {
	Draft: "gray",
	Submitted: "blue",
	Cancelled: "red",
	Paid: "green",
	Unpaid: "orange",
	Rejected: "red",
}

const approvalStatusMap = {
	Approved: "green",
	Rejected: "red",
	Draft: "orange",
}

const claimTitle = computed(() => {
	let title = props.doc.expense_type
	if (props.doc.total_expenses > 1) {
		title += ` & ${props.doc.total_expenses - 1} more`
	}

	return title
})

const claimDates = computed(() => {
	if (!props.doc.from_date && !props.doc.to_date)
		return dayjs(props.doc.posting_date).format("D MMM")

	if (props.doc.from_date === props.doc.to_date) {
		return dayjs(props.doc.from_date).format("D MMM")
	} else {
		return `${dayjs(props.doc.from_date).format("D MMM")} - ${dayjs(
			props.doc.to_date
		).format("D MMM")}`
	}
})

const currency = computed(() => getCompanyCurrencySymbol(props.doc.company))

const approvalStatus = computed(() => {
	return props.doc.approval_status === "Draft"
		? "Pending"
		: props.doc.approval_status
})
</script>
