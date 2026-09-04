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
					<template v-if="documents.data?.length">
						<div class="flex flex-row items-center justify-between w-full">
							<span class="text-gray-600 text-sm font-medium leading-5">
								{{ isSelecting ? __("{0} selected", [selectedSlips.length]) : "" }}
							</span>
							<div class="flex flex-row items-center gap-2">
								<Button v-if="isSelecting" variant="ghost" @click="toggleSelectAll">
									{{ areAllSelected ? __("Clear") : __("Select All") }}
								</Button>
								<Button variant="ghost" @click="toggleSelectionMode">
									{{ isSelecting ? __("Cancel") : __("Select") }}
								</Button>
							</div>
						</div>

						<div class="flex flex-col bg-white rounded mt-3 overflow-auto w-full">
							<div
								class="p-3.5 items-center justify-between border-b cursor-pointer"
								v-for="link in documents.data"
								:key="link.name"
							>
								<div v-if="isSelecting" @click="toggleSelection(link.name)">
									<SalarySlipItem
										:doc="link"
										selectable
										:selected="selectedSlips.includes(link.name)"
									/>
								</div>
								<router-link
									v-else
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

						<div v-if="isSelecting" class="sticky bottom-4 w-full mt-5">
							<ErrorMessage :message="downloadError" class="mb-2" />
							<Button
								class="w-full rounded py-5 text-base disabled:bg-gray-700 disabled:text-white"
								variant="solid"
								:loading="isDownloading"
								:disabled="!selectedSlips.length"
								@click="downloadSelected"
							>
								{{ downloadLabel }}
							</Button>
						</div>
					</template>
					<EmptyState :message="__('No salary slips found')" v-else />
				</div>
			</div>
		</template>
	</BaseLayout>
</template>

<script setup>
import { inject, ref, computed, watch, onMounted, onBeforeUnmount } from "vue"
import { Autocomplete, ErrorMessage, createListResource } from "frappe-ui"

import BaseLayout from "@/components/BaseLayout.vue"
import EmptyState from "@/components/EmptyState.vue"
import SalarySlipItem from "@/components/SalarySlipItem.vue"

import { downloadBulkPDF } from "@/utils/download"
import { formatCurrency } from "@/utils/formatters"

let selectedPeriod = ref({})
let periodsByName = ref({})

const isSelecting = ref(false)
const selectedSlips = ref([])
const isDownloading = ref(false)
const downloadError = ref("")

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

const areAllSelected = computed(
	() => selectedSlips.value.length === documents.data?.length
)

const downloadLabel = computed(() => {
	const count = selectedSlips.value.length
	if (!count) return __("Download Salary Slips")
	if (count === 1) return __("Download Salary Slip")
	return __("Download {0} Salary Slips", [count])
})

function toggleSelectionMode() {
	isSelecting.value = !isSelecting.value
	resetSelection()
}

function resetSelection() {
	selectedSlips.value = []
	downloadError.value = ""
}

function toggleSelection(name) {
	const index = selectedSlips.value.indexOf(name)
	if (index === -1) selectedSlips.value.push(name)
	else selectedSlips.value.splice(index, 1)

	downloadError.value = ""
}

function toggleSelectAll() {
	if (areAllSelected.value) selectedSlips.value = []
	else selectedSlips.value = documents.data.map((slip) => slip.name)

	downloadError.value = ""
}

async function downloadSelected() {
	isDownloading.value = true
	downloadError.value = ""

	const period = selectedPeriod.value?.value?.replace(/\s/g, "-")

	try {
		await downloadBulkPDF(
			"Salary Slip",
			selectedSlips.value,
			`Salary-Slips-${period}.pdf`
		)
		toggleSelectionMode()
	} catch (error) {
		downloadError.value = __("Failed to download PDF: {0}", [error.message])
	} finally {
		isDownloading.value = false
	}
}

function getPeriodLabel(period) {
	return `${dayjs(period?.start_date).format("MMM YYYY")} - ${dayjs(
		period?.end_date
	).format("MMM YYYY")}`
}

watch(
	() => selectedPeriod.value,
	(value) => {
		resetSelection()

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
			resetSelection()
			documents.reload()
		}
	})
})

onBeforeUnmount(() => {
	socket.off("hrms:update_salary_slips")
})
</script>
