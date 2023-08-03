<template>
	<div class="flex flex-col w-full">
		<div class="text-xl text-gray-800 font-bold">Expense Claim Summary</div>
		<div class="flex flex-col gap-4 bg-white py-3 px-3.5 mt-3 rounded-xl">
			<div class="flex flex-col gap-1.5">
				<span class="text-gray-600 text-base font-medium leading-5"
					>Total Expense Amount</span
				>
				<span class="text-gray-800 text-2xl font-bold leading-6">
					{{ `${company_currency} ${total_claimed_amount}` }}
				</span>
			</div>

			<div class="flex flex-row justify-between">
				<div class="flex flex-col gap-1">
					<div class="flex flex-row gap-1 items-center">
						<span class="text-gray-600 text-sm font-medium leading-5"
							>Pending</span
						>
						<FeatherIcon name="alert-circle" class="text-yellow-500 h-3 w-3" />
					</div>
					<span class="text-gray-800 text-xl font-semibold leading-6">
						{{ `${company_currency} ${summary.data?.total_pending_amount}` }}
					</span>
				</div>
				<div class="flex flex-col gap-1">
					<div class="flex flex-row gap-1 items-center">
						<span class="text-gray-600 text-sm font-medium leading-5"
							>Approved</span
						>
						<FeatherIcon name="check-circle" class="text-green-500 h-3 w-3" />
					</div>
					<span class="text-gray-800 text-xl font-semibold leading-6">
						{{ `${company_currency} ${summary.data?.total_approved_amount}` }}
					</span>
				</div>

				<div class="flex flex-col gap-1">
					<div class="flex flex-row gap-1 items-center">
						<span class="text-gray-600 text-sm font-medium leading-5">
							Rejected
						</span>
						<FeatherIcon name="x-circle" class="text-red-500 h-3 w-3" />
					</div>
					<span class="text-gray-800 text-xl font-semibold leading-6">
						{{
							`${summary.data?.currency} ${summary.data?.total_rejected_amount}`
						}}
					</span>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { FeatherIcon, createResource } from "frappe-ui"
import { computed, inject } from "vue"

import { getCompanyCurrency } from "@/data/company"

const employee = inject("$employee")

const summary = createResource({
	url: "hrms.api.get_expense_claim_summary",
	params: {
		employee: employee.data.name,
	},
	auto: true,
})

const total_claimed_amount = computed(() => {
	return (
		summary.data?.total_pending_amount +
		summary.data?.total_approved_amount +
		summary.data?.total_rejected_amount
	)
})

const company_currency = computed(() =>
	getCompanyCurrency(employee.data.company)
)
</script>
