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
			>
				<!-- Expenses child table -->
				<template #expenses>
					<!-- Header -->
					<div class="flex flex-row justify-between items-center">
						<h2 class="text-lg font-semibold text-gray-800">Expenses</h2>
						<div class="flex flex-row gap-3 items-center">
							<span class="text-lg font-semibold text-gray-800">
								{{`${currency} ${expenseClaim.total_claimed_amount || 0}`}}
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
			</FormView>
		</ion-content>
	</ion-page>
</template>

<script setup>
import { IonPage, IonContent, IonModal, modalController } from "@ionic/vue"
import { createResource, FeatherIcon } from "frappe-ui"
import { computed, ref, watch, inject } from "vue"

import FormView from "@/components/FormView.vue"
import AddExpenseActionSheet from "@/components/AddExpenseActionSheet.vue"

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

// reactive object to store form data
const expenseClaim = ref({
	employee: employee.data.name,
	company: employee.data.company,
})

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

const tabs = [
	{
		name: "Expenses",
		lastField: "taxes",
	},
	{
		name: "Advances",
		lastField: "advances",
	},
	{
		name: "Totals",
		lastField: "cost_center",
	},
]

const currency = computed(() => getCompanyCurrency(expenseClaim.value.company))

// form scripts

// helper functions
function getFilteredFields(fields) {
	// reduce noise from the form view by excluding unnecessary fields
	// ex: employee and other details can be fetched from the session user
	const excludeFields = ["naming_series", "task"]
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

function calculateTotals() {
	let total_claimed_amount = 0
	let total_sanctioned_amount = 0

	expenseClaim.value?.expenses?.forEach((item) => {
		total_claimed_amount += parseFloat(item.amount)
		total_sanctioned_amount += parseFloat(item.sanctioned_amount)
	})

	expenseClaim.value.total_claimed_amount = total_claimed_amount
	expenseClaim.value.total_sanctioned_amount = total_sanctioned_amount
}
</script>
