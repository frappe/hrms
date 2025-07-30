<template>
	<BaseLayout :pageTitle="__('Salary Slips')">
		<template #body>
			<div class="flex flex-col items-center my-7 p-4">
				<div class="flex flex-col w-full bg-white rounded py-5 px-3.5 gap-5">
					<div v-if="lastSalarySlip && lastSalarySlip.year_to_date" class="flex flex-col w-full gap-1.5">
						<span class="text-gray-600 text-sm font-medium leading-5">
							{{ __("Year To Date") }}
						</span>
						<span class="text-gray-800 text-xl font-bold leading-6">
							{{
								formatCurrency(
									lastSalarySlip.year_to_date,
									lastSalarySlip.currency
								)
							}}
						</span>
					</div>

					<Autocomplete
						:label="__('Payroll Period')"
						class="w-full"
						:placeholder="__('Select Payroll Period')"
						v-model="selectedPeriod"
						:options="payrollPeriods.data"
					/>
				</div>

				<div class="flex flex-col items-center mt-5 mb-7 w-full">
					<div
						v-if="documents.data?.length"
						class="flex flex-col bg-white rounded mt-5 overflow-auto w-full"
					>
						<div
							class="p-3.5 items-center justify-between border-b cursor-pointer"
							v-for="link in documents.data"
							:key="link.name"
						>
							<router-link
								:to="{
									name: 'SalarySlipDetailView',
									params: { id: link.name },
								}"
								v-slot="{ navigate }"
							>
								<SalarySlipItem :doc="link" @click="navigate" />
							</router-link>
						</div>
					</div>
					<EmptyState :message="__('No salary slips found')" v-else />
				</div>
			</div>
		</template>
	</BaseLayout>
</template>

<script setup>
import { inject, ref, computed, watch, onMounted, onBeforeUnmount } from "vue"
import { Autocomplete, createListResource } from "frappe-ui"

import BaseLayout from "@/components/BaseLayout.vue"
import EmptyState from "@/components/EmptyState.vue"
import SalarySlipItem from "@/components/SalarySlipItem.vue"

import { formatCurrency } from "@/utils/formatters"

let selectedPeriod = ref({})
let periodsByName = ref({})

const employee = inject("$employee")
const dayjs = inject("$dayjs")
const socket = inject("$socket")
const __ = inject("$translate")

const payrollPeriods = createListResource({
	doctype: "Payroll Period",
	fields: ["name", "start_date", "end_date"],
	filters: {
		company: employee.data?.company,
	},
	orderBy: "start_date desc",
	auto: true,
	transform(data) {
		return data.map((period) => {
			periodsByName.value[period.name] = period
			return {
				label: getPeriodLabel(period),
				value: period.name,
			}
		})
	},
	onSuccess: (data) => {
		selectedPeriod.value = data[0]
	},
})

const documents = createListResource({
	doctype: "Salary Slip",
	fields: [
		"name",
		"start_date",
		"end_date",
		"currency",
		"gross_pay",
		"net_pay",
		"year_to_date",
	],
	filters: {
		employee: employee.data?.name,
		docstatus: 1,
	},
	orderBy: "end_date desc",
})

const lastSalarySlip = computed(() => documents.data?.[0])

function getPeriodLabel(period) {
	return `${dayjs(period?.start_date).format("MMM YYYY")} - ${dayjs(
		period?.end_date
	).format("MMM YYYY")}`
}

watch(
	() => selectedPeriod.value,
	(value) => {
		let period = periodsByName.value[value?.value]
		documents.filters.start_date = [
			"between",
			[period?.start_date, period?.end_date],
		]
		documents.reload()
	}
)

onMounted(() => {
	socket.on("hrms:update_salary_slips", (data) => {
		if (data.employee === employee.data.name) {
			documents.reload()
		}
	})
})

onBeforeUnmount(() => {
	socket.off("hrms:update_salary_slips")
})
</script>
