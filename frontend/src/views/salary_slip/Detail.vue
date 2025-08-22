<template>
	<ion-page>
		<ion-content :fullscreen="true">
			<FormView
				v-if="formFields.data"
				doctype="Salary Slip"
				v-model="salarySlip"
				:fields="formFields.data"
				:id="props.id"
				:tabbedView="true"
				:tabs="tabs"
				:showFormButton="false"
			>
				<!-- Child Tables -->
				<template #earnings="{ isFormReadOnly }">
					<SalaryDetailTable
						type="Earnings"
						:salarySlip="salarySlip"
						:isReadOnly="isFormReadOnly"
					/>
				</template>

				<template #deductions="{ isFormReadOnly }">
					<SalaryDetailTable
						type="Deductions"
						:salarySlip="salarySlip"
						:isReadOnly="isFormReadOnly"
					/>
				</template>

				<template #formButton>
					<ErrorMessage :message="downloadError" class="mt-2" />
					<Button
						class="w-full rounded py-5 text-base disabled:bg-gray-700 disabled:text-white"
						@click="downloadPDF"
						variant="solid"
						:loading="loading"
					>
						{{ __("Download PDF") }}
					</Button>
				</template>
			</FormView>
		</ion-content>
	</ion-page>
</template>

<script setup>
import { ref, watch } from "vue"
import { IonPage, IonContent } from "@ionic/vue"

import { createResource, ErrorMessage } from "frappe-ui"

import FormView from "@/components/FormView.vue"
import SalaryDetailTable from "@/components/SalaryDetailTable.vue"

import { getCompanyCurrency } from "@/data/currencies"

const props = defineProps({
	id: {
		type: String,
		required: true,
	},
})

const downloadError = ref("")
const loading = ref(false)

// reactive object to store form data
const salarySlip = ref({})

// get form fields
const formFields = createResource({
	url: "hrms.api.get_doctype_fields",
	params: { doctype: "Salary Slip" },
	transform(data) {
		return getFilteredFields(data)
	},
})
formFields.reload()

const tabs = [
	{ name: "Details", lastField: "payment_days" },
	{ name: "Earnings & Deductions", lastField: "base_total_deduction" },
	{ name: "Net Pay Info", lastField: "base_total_in_words" },
	{ name: "Income Tax Breakup", lastField: "total_income_tax" },
	{ name: "Bank Details", lastField: "bank_account_no" },
]

watch(
	() => salarySlip.value.company,
	async (company) => {
		if (!company) return

		const companyCurrency = await getCompanyCurrency(company)

		formFields.data?.map((field) => {
			if (field.label?.includes("Company Currency")) {
				if (salarySlip.value.currency === companyCurrency) {
					// hide base currency fields
					field.hidden = true
				} else {
					// set currency in label
					field.label = field.label.replace("Company Currency", companyCurrency)
				}
			}
		})
	},
	{ immediate: true }
)

function getFilteredFields(fields) {
	const hasTimesheets = salarySlip.value?.timesheets?.length
	if (hasTimesheets) return fields

	const excludeFields = [
		"timesheets_section",
		"timesheets",
		"total_working_hours",
		"hour_rate",
		"base_hour_rate",
		"help_section",
		"earning_deduction_sb",
	]
	return fields.filter((field) => !excludeFields.includes(field.fieldname))
}

function downloadPDF() {
	const salarySlipName = salarySlip.value.name
	loading.value = true

	let headers = { "X-Frappe-Site-Name": window.location.hostname }
	if (window.csrf_token) {
		headers["X-Frappe-CSRF-Token"] = window.csrf_token
	}

	fetch("/api/method/hrms.api._download_pdf", {
		method: "POST",
		headers,
		body: new URLSearchParams({doctype: "Salary Slip" ,docname: salarySlipName }),
		responseType: "blob",
	})
		.then((response) => {
			if (response.ok) {
				return response.blob()
			} else {
				downloadError.value = "Failed to download PDF"
			}
		})
		.then((blob) => {
			if (!blob) return
			const blobUrl = window.URL.createObjectURL(blob)
			const link = document.createElement("a")
			link.href = blobUrl
			link.download = `${salarySlipName}.pdf`
			link.click()

			setTimeout(() => {
				window.URL.revokeObjectURL(blobUrl)
			}, 3000)
		})
		.catch((error) => {
			downloadError.value = `Failed to download PDF: ${error.message}`
		})
		.finally(() => {
			loading.value = false
		})
}
</script>
