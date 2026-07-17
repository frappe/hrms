<template>
	<div class="flex flex-col w-full gap-5" v-if="summary.data">
		<div class="text-lg-bold text-gray-800">{{ __("Expense Claim Summary") }}</div>
		<div
			class="flex flex-col gap-4 bg-white py-3 px-3.5 rounded-lg border-none"
		>
			<div class="flex flex-col gap-1.5">
				<span class="text-gray-600 text-base-medium leading-5">
					{{ __("Total Claimed Amount") }}
				</span>
				<span class="text-gray-800 text-lg-bold leading-6">
					{{ formatCurrency(total_claimed_amount, company_currency) }}
				</span>
			</div>

			<div class="flex flex-row justify-between">
				<div class="flex flex-col gap-1">
					<div class="flex flex-row gap-1 items-center">
						<span class="text-gray-600 text-sm-medium leading-5">
							{{ __("Pending") }}
						</span>
						<span class="lucide-alert-circle text-yellow-500 h-3 w-3" />
					</div>
					<span class="text-gray-800 text-base-semibold leading-6">
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
						<span class="text-gray-600 text-sm-medium leading-5">
							{{ __("Approved") }}
						</span>
						<span class="lucide-check-circle text-green-500 h-3 w-3" />
					</div>
					<span class="text-gray-800 text-base-semibold leading-6">
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
						<span class="text-gray-600 text-sm-medium leading-5">
							{{ __("Rejected") }}
						</span>
						<span class="lucide-x-circle text-red-500 h-3 w-3" />
					</div>
					<span class="text-gray-800 text-base-semibold leading-6">
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
