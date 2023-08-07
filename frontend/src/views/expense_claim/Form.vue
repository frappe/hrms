<template>
	<ion-page>
		<ion-content :fullscreen="true">
			<FormView
				v-if="formFields.data"
				doctype="Expense Claim"
				v-model="expenseClaim"
				:fields="formFields.data"
				:id="props.id"
				:tabbedView="true"
				:tabs="tabs"
				@validateForm="validateForm"
			>
				<!-- Child Tables -->
				<template #expenses>
					<ExpensesTable
						v-model:expenseClaim="expenseClaim"
						:currency="currency"
						@addExpenseItem="addExpenseItem"
					/>
				</template>

				<template #taxes>
					<ExpenseTaxesTable
						v-model:expenseClaim="expenseClaim"
						:currency="currency"
						@addExpenseTax="addExpenseTax"
					/>
				</template>

				<template #advances>
					<ExpenseAdvancesTable
						v-model:expenseClaim="expenseClaim"
						:currency="currency"
					/>
				</template>
			</FormView>
		</ion-content>
	</ion-page>
</template>

<script setup>
import { IonPage, IonContent, modalController } from "@ionic/vue"
import { createResource } from "frappe-ui"
import { computed, ref, watch, inject } from "vue"

import FormView from "@/components/FormView.vue"
import ExpensesTable from "@/components/ExpensesTable.vue"
import ExpenseTaxesTable from "@/components/ExpenseTaxesTable.vue"
import ExpenseAdvancesTable from "@/components/ExpenseAdvancesTable.vue"

import { getCompanyCurrency } from "@/data/currencies"

const dayjs = inject("$dayjs")
const employee = inject("$employee")
const today = dayjs().format("YYYY-MM-DD")

const props = defineProps({
	id: {
		type: String,
		required: false,
	},
})

const tabs = [
	{ name: "Expenses", lastField: "taxes" },
	{ name: "Advances", lastField: "advances" },
	{ name: "Totals", lastField: "cost_center" },
]

// reactive object to store form data
const expenseClaim = ref({
	employee: employee.data.name,
	company: employee.data.company,
})

const currency = computed(() => getCompanyCurrency(expenseClaim.value.company))

// get form fields
const formFields = createResource({
	url: "hrms.api.get_doctype_fields",
	params: { doctype: "Expense Claim" },
	transform(data) {
		let fields = getFilteredFields(data)

		return fields.map((field) => {
			if (field.fieldname === "posting_date") field.default = today

			return field
		})
	},
})
formFields.reload()

// resources
const advances = createResource({
	url: "hrms.hr.doctype.expense_claim.expense_claim.get_advances",
	params: { employee: employee.data.name },
	onSuccess(data) {
		// set advances
		expenseClaim.value.advances = []
		data.forEach((advance) => {
			expenseClaim.value.advances.push({
				employee_advance: advance.name,
				purpose: advance.purpose,
				posting_date: advance.posting_date,
				advance_account: advance.advance_account,
				advance_paid: advance.paid_amount,
				unclaimed_amount: advance.paid_amount - advance.claimed_amount,
				allocated_amount: 0,
			})
		})
	},
})

// form scripts
watch(
	() => expenseClaim.value.employee && !props.id,
	(_value) => {
		advances.reload()
	},
	{ immediate: true }
)

// helper functions
function getFilteredFields(fields) {
	// reduce noise from the form view by excluding unnecessary fields
	// ex: employee and other details can be fetched from the session user
	const excludeFields = [
		"naming_series",
		"task",
		"taxes_and_charges_sb",
		"advance_payments_sb",
	]
	const extraFields = [
		"employee",
		"employee_name",
		"department",
		"company",
		"remark",
		"is_paid",
		"mode_of_payment",
		"clearance_date",
	]

	if (!props.id) excludeFields.push(...extraFields)

	return fields.filter((field) => !excludeFields.includes(field.fieldname))
}

function addExpenseItem(item) {
	if (!expenseClaim.value.expenses) expenseClaim.value.expenses = []
	expenseClaim.value.expenses.push(item)
	calculateTotals()
	modalController.dismiss()
}

function addExpenseTax(item) {
	if (!expenseClaim.value.taxes) expenseClaim.value.taxes = []
	expenseClaim.value.taxes.push(item)
	calculateTaxes()
	modalController.dismiss()
}

function calculateTotals() {
	let total_claimed_amount = 0
	let total_sanctioned_amount = 0

	expenseClaim.value?.expenses?.forEach((item) => {
		total_claimed_amount += parseFloat(item.amount)
		total_sanctioned_amount += parseFloat(item.sanctioned_amount)
	})

	expenseClaim.value.total_claimed_amount = total_claimed_amount
	expenseClaim.value.total_sanctioned_amount = total_sanctioned_amount
	calculateGrandTotal()
}

function calculateTaxes() {
	let total_taxes_and_charges = 0

	expenseClaim.value?.taxes?.forEach((item) => {
		if (item.rate)
			item.tax_amount =
				parseFloat(expenseClaim.value.total_sanctioned_amount) *
				parseFloat(item.rate / 100)

		item.total =
			parseFloat(item.tax_amount) +
			parseFloat(expenseClaim.value.total_sanctioned_amount)
		total_taxes_and_charges += parseFloat(item.tax_amount)
	})
	expenseClaim.value.total_taxes_and_charges = total_taxes_and_charges
	calculateGrandTotal()
}

function calculateGrandTotal() {
	expenseClaim.value.grand_total =
		parseFloat(expenseClaim.value.total_sanctioned_amount || 0) +
		parseFloat(expenseClaim.value.total_taxes_and_charges || 0) -
		parseFloat(expenseClaim.value.total_advance_amount || 0)

	setAdvanceAmount()
}

function setAdvanceAmount() {
	let amount_to_be_allocated = parseFloat(expenseClaim.value.grand_total)

	expenseClaim?.value?.advances?.forEach((advance) => {
		if (amount_to_be_allocated >= parseFloat(advance.unclaimed_amount)) {
			advance.allocated_amount = parseFloat(advance.unclaimed_amount)
			amount_to_be_allocated -= parseFloat(advance.allocated_amount)
		} else {
			advance.allocated_amount = amount_to_be_allocated
			amount_to_be_allocated = 0
		}

		advance.selected = advance.allocated_amount > 0 ? true : false
	})
}

function validateForm() {
	// set selected advances
	expenseClaim.value.advances = expenseClaim.value.advances.filter(
		(advance) => advance.selected
	)
}
</script>
