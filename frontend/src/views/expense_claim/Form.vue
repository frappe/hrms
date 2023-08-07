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
				<!-- Expenses child table -->
				<template #expenses>
					<!-- Header -->
					<div class="flex flex-row justify-between items-center">
						<h2 class="text-lg font-semibold text-gray-800">Expenses</h2>
						<div class="flex flex-row gap-3 items-center">
							<span class="text-lg font-semibold text-gray-800">
								{{ `${currency} ${expenseClaim.total_claimed_amount || 0}` }}
							</span>
							<Button
								id="add-expense-modal"
								class="text-sm"
								icon="plus"
								appearance="secondary"
							/>
						</div>
					</div>

					<!-- table -->
					<div
						v-if="expenseClaim.expenses"
						class="flex flex-col bg-white mt-5 rounded-lg border overflow-auto"
					>
						<div
							class="flex flex-row p-3.5 items-center justify-between border-b cursor-pointer"
							v-for="item in expenseClaim.expenses"
							:key="item.name"
						>
							<div class="flex flex-col w-full justify-center gap-2.5">
								<div class="flex flex-row items-center justify-between">
									<div class="flex flex-row items-start gap-3 grow">
										<div class="flex flex-col items-start">
											<div class="text-lg font-normal text-gray-800">
												{{ item.expense_type }}
											</div>
											<div class="text-sm font-normal text-gray-500">
												<span>
													{{
														`Sanctioned: ${currency} ${
															item.sanctioned_amount || 0
														}`
													}}
												</span>
												<span class="whitespace-pre"> &middot; </span>
												<span class="whitespace-nowrap">
													{{ dayjs(item.expense_date).format("D MMM") }}
												</span>
											</div>
										</div>
									</div>
									<div class="flex flex-row justify-end items-center gap-2">
										<span class="text-gray-700 font-normal rounded-lg text-lg">
											{{ `${currency} ${item.amount}` }}
										</span>
										<FeatherIcon
											name="chevron-right"
											class="h-5 w-5 text-gray-500"
										/>
									</div>
								</div>
							</div>
						</div>
					</div>
					<EmptyState v-else message="No expense added" />

					<ion-modal
						ref="modal"
						trigger="add-expense-modal"
						:initial-breakpoint="1"
						:breakpoints="[0, 1]"
					>
						<!-- Filter Action Sheet -->
						<AddExpenseActionSheet
							:fields="expensesTableFields.data"
							@addExpenseItem="addExpenseItem"
						/>
					</ion-modal>
				</template>

				<template #taxes>
					<template v-if="expenseClaim.expenses">
						<div class="flex flex-row justify-between items-center">
							<h2 class="text-lg font-semibold text-gray-800">
								Taxes & Charges
							</h2>
							<div class="flex flex-row gap-3 items-center">
								<span class="text-lg font-semibold text-gray-800">
									{{
										`${currency} ${expenseClaim.total_taxes_and_charges || 0}`
									}}
								</span>
								<Button
									id="add-taxes-modal"
									class="text-sm"
									icon="plus"
									appearance="secondary"
								/>
							</div>
						</div>

						<div
							v-if="expenseClaim.taxes"
							class="flex flex-col bg-white mt-5 rounded-lg border overflow-auto"
						>
							<div
								class="flex flex-row p-3.5 items-center justify-between border-b cursor-pointer"
								v-for="item in expenseClaim.taxes"
								:key="item.name"
							>
								<div class="flex flex-col w-full justify-center gap-2.5">
									<div class="flex flex-row items-center justify-between">
										<div class="flex flex-row items-start gap-3 grow">
											<div class="flex flex-col items-start">
												<div class="text-lg font-normal text-gray-800">
													{{ item.account_head }}
												</div>
												<div class="text-sm font-normal text-gray-500">
													<span>
														{{ `Rate: ${currency} ${item.rate || 0}` }}
													</span>
													<span class="whitespace-pre"> &middot; </span>
													<span class="whitespace-nowrap">
														{{ `Amount: ${currency} ${item.tax_amount || 0}` }}
													</span>
												</div>
											</div>
										</div>
										<div class="flex flex-row justify-end items-center gap-2">
											<span
												class="text-gray-700 font-normal rounded-lg text-lg"
											>
												{{ `${currency} ${item.total}` }}
											</span>
											<FeatherIcon
												name="chevron-right"
												class="h-5 w-5 text-gray-500"
											/>
										</div>
									</div>
								</div>
							</div>
						</div>
						<EmptyState v-else message="No taxes added" />

						<ion-modal
							ref="modal"
							trigger="add-taxes-modal"
							:initial-breakpoint="1"
							:breakpoints="[0, 1]"
						>
							<AddExpenseTaxActionSheet
								:fields="taxesTableFields.data"
								:totalSanctionedAmount="expenseClaim.total_sanctioned_amount"
								@addExpenseTax="addExpenseTax"
							/>
						</ion-modal>
					</template>
				</template>

				<template #advances>
					<div class="flex flex-row justify-between items-center">
						<h2 class="text-lg font-semibold text-gray-800">
							Settle against Advances
						</h2>
					</div>

					<div class="flex flex-col gap-2.5">
						<!-- Advance Card -->
						<div
							v-for="advance in expenseClaim.advances"
							:key="advance.name"
							class="flex flex-col bg-white border shadow-sm rounded-lg p-3.5 cursor-pointer"
							:class="advance.selected ? 'border-blue-500' : ''"
							@click="advance.selected = !advance.selected"
						>
							<div class="flex flex-row justify-between items-center">
								<div class="flex flex-row items-start gap-3">
									<Input
										type="checkbox"
										class="mt-0.5"
										v-model="advance.selected"
									/>

									<div class="flex flex-col items-start gap-1">
										<div class="text-lg font-semibold text-gray-800">
											{{ advance.purpose || advance.employee_advance }}
										</div>
										<div
											class="flex flex-row items-center gap-3 justify-between"
										>
											<div class="text-sm font-normal text-gray-500">
												{{
													`Unclaimed Amount: ${currency} ${advance.unclaimed_amount}`
												}}
											</div>
										</div>
									</div>
								</div>

								<div class="flex flex-row items-center gap-2">
									<span class="text-normal">
										{{ currency }}
									</span>
									<Input
										type="number"
										class="w-20"
										v-model="advance.allocated_amount"
										@input="(v) => (advance.selected = v)"
									/>
								</div>
							</div>
						</div>
					</div>
				</template>
			</FormView>
		</ion-content>
	</ion-page>
</template>

<script setup>
import { IonPage, IonContent, IonModal, modalController } from "@ionic/vue"
import { createResource, FeatherIcon, Input } from "frappe-ui"
import { computed, ref, watch, inject } from "vue"

import FormView from "@/components/FormView.vue"
import AddExpenseActionSheet from "@/components/AddExpenseActionSheet.vue"
import AddExpenseTaxActionSheet from "@/components/AddExpenseTaxActionSheet.vue"

import { getCompanyCurrency } from "@/data/currencies"
import EmptyState from "@/components/EmptyState.vue"

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

const expensesTableFields = createResource({
	url: "hrms.api.get_doctype_fields",
	params: { doctype: "Expense Claim Detail" },
	transform(data) {
		const excludeFields = ["description_sb", "amounts_sb"]
		const dimensionFields = [
			"cost_center",
			"project",
			"branch",
			"accounting_dimensions_section",
		]

		if (!props.id) excludeFields.push(...dimensionFields)

		return data.filter((field) => !excludeFields.includes(field.fieldname))
	},
})
expensesTableFields.reload()

const taxesTableFields = createResource({
	url: "hrms.api.get_doctype_fields",
	params: { doctype: "Expense Taxes and Charges" },
	transform(data) {
		const excludeFields = ["description_sb"]
		const dimensionFields = [
			"cost_center",
			"project",
			"accounting_dimensions_section",
		]

		if (!props.id) excludeFields.push(...dimensionFields)

		return data.filter((field) => !excludeFields.includes(field.fieldname))
	},
})
taxesTableFields.reload()

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
