<template>
	<div class="flex flex-col w-full gap-5" v-if="summary.data">
		<div class="text-lg text-gray-800 font-bold">{{ __("Expense Claim Summary") }}</div>
		<div
			class="flex flex-col gap-4 bg-white py-3 px-3.5 rounded-lg border-none"
		>
			<div class="flex flex-col gap-1.5">
				<span class="text-gray-600 text-base font-medium leading-5">
					{{ __("Total Claimed Amount") }}
				</span>
				<span class="text-gray-800 text-lg font-bold leading-6">
					{{ formatCurrency(total_claimed_amount, company_currency) }}
				</span>
			</div>

			<div class="flex flex-row justify-between">
				<div class="flex flex-col gap-1">
					<div class="flex flex-row gap-1 items-center">
						<span class="text-gray-600 text-sm font-medium leading-5">
							{{ __("Pending") }}
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
							{{ __("Approved") }}
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
							{{ __("Rejected") }}
						</span>
						<FeatherIcon name="x-circle" class="text-red-500 h-3 w-3" />
					</div>
					<span class="text-gray-800 text-base font-semibold leading-6">
						{{
							formatCurrency(
								summary.data?.total_rejected_amount + 
								(summary.data?.total_claimed_in_approved - summary.data?.total_approved_amount),
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
import { FeatherIcon } from "frappe-ui"
import { computed } from "vue"

import { expenseClaimSummary as summary } from "@/data/claims"

import { formatCurrency } from "@/utils/formatters"

const total_claimed_amount = computed(() => {
	return (
		summary.data?.total_pending_amount +
		summary.data?.total_claimed_in_approved +
		summary.data?.total_rejected_amount
	)
})

const company_currency = computed(() => summary.data?.currency)
</script>
