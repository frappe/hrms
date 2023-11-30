<template>
	<div class="flex flex-col w-full gap-5" v-if="summary.data">
		<div class="text-lg text-gray-800 font-bold">Expense Claim Summary</div>
		<div
			class="flex flex-col gap-4 bg-white py-3 px-3.5 rounded-lg border-none"
		>
			<div class="flex flex-col gap-1.5">
				<span class="text-gray-600 text-base font-medium leading-5">
					Total Expense Amount
				</span>
				<span class="text-gray-800 text-lg font-bold leading-6">
					{{ formatCurrency(total_claimed_amount, company_currency) }}
				</span>
			</div>

			<div class="flex flex-row justify-between">
				<div class="flex flex-col gap-1">
					<div class="flex flex-row gap-1 items-center">
						<span class="text-gray-600 text-sm font-medium leading-5">
							Pending
						</span>
						<FeatherIcon name="alert-circle" class="text-yellow-500 h-3 w-3" />
					</div>
					<span class="text-gray-800 text-base font-semibold leading-6">
						{{
							formatCurrency(
								summary.data?.total_pending_amount,
								company_currency
							)
						}}
					</span>
				</div>
				<div class="flex flex-col gap-1">
					<div class="flex flex-row gap-1 items-center">
						<span class="text-gray-600 text-sm font-medium leading-5">
							Approved
						</span>
						<FeatherIcon name="check-circle" class="text-green-500 h-3 w-3" />
					</div>
					<span class="text-gray-800 text-base font-semibold leading-6">
						{{
							formatCurrency(
								summary.data?.total_approved_amount,
								company_currency
							)
						}}
					</span>
				</div>

				<div class="flex flex-col gap-1">
					<div class="flex flex-row gap-1 items-center">
						<span class="text-gray-600 text-sm font-medium leading-5">
							Rejected
						</span>
						<FeatherIcon name="x-circle" class="text-red-500 h-3 w-3" />
					</div>
					<span class="text-gray-800 text-base font-semibold leading-6">
						{{
							formatCurrency(
								summary.data?.total_rejected_amount,
								company_currency
							)
						}}
					</span>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { FeatherIcon, createResource } from "frappe-ui"
import { computed, inject, onMounted, onBeforeUnmount } from "vue"

import { formatCurrency } from "@/utils/formatters"

const employee = inject("$employee")
const socket = inject("$socket")

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

const company_currency = computed(() => summary.data?.currency)

onMounted(() => {
	socket.on("hrms:update_expense_claims", (data) => {
		if (data.employee === employee.data.name) {
			summary.reload()
		}
	})
})

onBeforeUnmount(() => {
	socket.off("hrms:update_expense_claims")
})
</script>
