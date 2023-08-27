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
			</FormView>

			<div
				class="px-4 pt-4 mt-2 sm:w-96 bg-white sticky bottom-0 w-full drop-shadow-xl z-40 border-t rounded-t-xl pb-10"
			>
				<ErrorMessage :message="downloadError" class="mt-2" />
				<Button
					class="w-full rounded-md py-2.5 px-3.5 mt-2"
					@click="downloadPDF"
					appearance="primary"
				>
					Download PDF
				</Button>
			</div>
		</ion-content>
	</ion-page>
</template>

<script setup>
import { computed, ref } from "vue"
import { IonPage, IonContent } from "@ionic/vue"

import { createResource, ErrorMessage } from "frappe-ui"

import FormView from "@/components/FormView.vue"
import SalaryDetailTable from "@/components/SalaryDetailTable.vue"

const props = defineProps({
	id: {
		type: String,
		required: true,
	},
})

const downloadError = ref("")
// reactive object to store form data
const salarySlip = ref({})

// get form fields
const formFields = createResource({
	url: "hrms.api.get_doctype_fields",
	params: { doctype: "Salary Slip" },
})
formFields.reload()

const tabs = [
	{ name: "Details", lastField: "payment_days" },
	{ name: "Earnings & Deductions", lastField: "base_total_deduction" },
	{ name: "Net Pay Info", lastField: "base_total_in_words" },
	{ name: "Income Tax Breakup", lastField: "total_income_tax" },
	{ name: "Bank Details", lastField: "bank_account_no" },
]

function downloadPDF() {
	const salarySlipName = salarySlip.value.name

	fetch("/api/method/hrms.api.download_salary_slip", {
		method: "POST",
		body: new URLSearchParams({ name: salarySlipName }),
		responseType: "blob",
	})
		.then((response) => {
			if (response.ok) {
				return response.blob()
			} else {
				downloadError.value = `Failed to download PDF: ${response.statusText}`
			}
		})
		.then((blob) => {
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
}
</script>
