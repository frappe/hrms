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
			<div class="flex flex-col gap-1.5">
				<span class="text-gray-600 text-base font-medium leading-5"> Fiscal Year </span>
				<Autocomplete
					label="Select Fiscal Year"
					class="w-full"
					placeholder="Select Fiscal Year"
					:options="fiscalYears.data.fiscal_years"
					v-model="selectedPeriod"
				/>
			</div>
		</div>
	</div>
</template>

<script setup>
import { FeatherIcon, Autocomplete } from "frappe-ui"
import { computed, ref, watch, inject, onMounted } from "vue"
import { formatCurrency } from "@/utils/formatters"
import { expenseClaimSummary as summary, fiscalYears } from "@/data/claims"

const dayjs = inject("$dayjs")

let selectedPeriod = ref({})

const total_claimed_amount = computed(() => {
	return (
		summary.data?.total_pending_amount +
		summary.data?.total_approved_amount +
		summary.data?.total_rejected_amount
	)
})

const fetchExpenseClaimSummary = (selectedPeriod) => {
	const year_start_date = selectedPeriod && selectedPeriod.year_start_date
	const year_end_date = selectedPeriod && selectedPeriod.year_end_date
	summary.reload({ year_start_date, year_end_date })
}

watch(
	() => selectedPeriod.value,
	(newValue) => {
		return fetchExpenseClaimSummary(newValue)
	},
	{ deep: true }
)

const company_currency = computed(() => summary.data?.currency)

onMounted(() => {
	selectedPeriod.value = fiscalYears.data.current_fiscal_year
	fetchExpenseClaimSummary(selectedPeriod.value)
})
</script>
