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
		</ion-content>
	</ion-page>
</template>

<script setup>
import { ref } from "vue"
import { IonPage, IonContent } from "@ionic/vue"

import FormView from "@/components/FormView.vue"
import SalaryDetailTable from "@/components/SalaryDetailTable.vue"

import { createResource } from "frappe-ui"

const props = defineProps({
	id: {
		type: String,
		required: true,
	},
})

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
</script>
