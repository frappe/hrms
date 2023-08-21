<template>
	<template v-if="expenseClaim.expenses">
		<div class="flex flex-row justify-between items-center pt-4">
			<h2 class="text-lg font-semibold text-gray-800">Taxes & Charges</h2>
			<div class="flex flex-row gap-3 items-center">
				<span class="text-lg font-semibold text-gray-800">
					{{ `${currency} ${expenseClaim.total_taxes_and_charges || 0}` }}
				</span>
				<Button
					id="add-taxes-modal"
					class="text-sm"
					icon="plus"
					appearance="secondary"
					@click="openModal()"
					:disabled="isReadOnly"
				/>
			</div>
		</div>

		<div
			v-if="expenseClaim.taxes?.length"
			class="flex flex-col bg-white mt-5 rounded-lg border overflow-auto"
		>
			<div
				class="flex flex-row p-3.5 items-center justify-between border-b cursor-pointer"
				v-for="(item, idx) in expenseClaim.taxes"
				:key="item.name"
				@click="openModal(item, idx)"
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
							<span class="text-gray-700 font-normal rounded-lg text-lg">
								{{ `${currency} ${item.total}` }}
							</span>
							<FeatherIcon name="chevron-right" class="h-5 w-5 text-gray-500" />
						</div>
					</div>
				</div>
			</div>
		</div>
		<EmptyState v-else message="No taxes added" />

		<ion-modal
			ref="modal"
			:is-open="isModalOpen"
			@didDismiss="resetSelectedItem()"
			:initial-breakpoint="1"
			:breakpoints="[0, 1]"
		>
			<!-- Add Expense Tax Action Sheet -->
			<div
				class="bg-white w-full flex flex-col items-center justify-center pb-5"
			>
				<div class="w-full pt-8 pb-5 border-b text-center">
					<span class="text-gray-900 font-bold text-xl">
						{{ modalTitle }}
					</span>
				</div>
				<div class="w-full flex flex-col items-center justify-center gap-5 p-4">
					<div class="flex flex-col w-full space-y-4">
						<FormField
							v-for="field in taxesTableFields.data"
							:key="field.fieldname"
							class="w-full"
							:label="field.label"
							:fieldtype="field.fieldtype"
							:fieldname="field.fieldname"
							:options="field.options"
							:linkFilters="field.linkFilters"
							:hidden="field.hidden"
							:reqd="field.reqd"
							:readOnly="field.read_only || isReadOnly"
							:default="field.default"
							v-model="expenseTax[field.fieldname]"
						/>
					</div>

					<div
						v-if="!isReadOnly"
						class="flex w-full flex-row items-center justify-between gap-3"
					>
						<Button
							v-if="editingIdx !== null"
							class="py-3 px-12 border-red-600 text-red-600"
							icon-left="trash"
							appearance="white"
							@click="deleteExpenseTax()"
						>
							Delete
						</Button>
						<Button
							appearance="primary"
							class="w-full py-3 px-12"
							:icon-left="editingIdx === null ? 'plus' : 'check'"
							@click="updateExpenseTax()"
							:disabled="addButtonDisabled"
						>
							{{ editingIdx === null ? "Add Tax" : "Update Tax" }}
						</Button>
					</div>
				</div>
			</div>
		</ion-modal>
	</template>
</template>

<script setup>
import { IonModal } from "@ionic/vue"
import { FeatherIcon, createResource } from "frappe-ui"
import { computed, ref, watch } from "vue"

import FormField from "@/components/FormField.vue"
import EmptyState from "@/components/EmptyState.vue"

const props = defineProps({
	expenseClaim: {
		type: Object,
		required: true,
	},
	currency: {
		type: String,
		required: true,
	},
	isReadOnly: {
		type: Boolean,
		default: false,
	},
})
const emit = defineEmits([
	"add-expense-tax",
	"update-expense-tax",
	"delete-expense-tax",
])
const expenseTax = ref({})
const editingIdx = ref(null)

const isModalOpen = ref(false)
const openModal = async (item, idx) => {
	if (item) {
		expenseTax.value = { ...item }
		editingIdx.value = idx
	}
	isModalOpen.value = true
}

const deleteExpenseTax = () => {
	emit("delete-expense-tax", editingIdx.value)
	resetSelectedItem()
}

const updateExpenseTax = () => {
	if (editingIdx.value === null) {
		emit("add-expense-tax", expenseTax.value)
	} else {
		emit("update-expense-tax", expenseTax.value, editingIdx.value)
	}
	resetSelectedItem()
}

function resetSelectedItem() {
	isModalOpen.value = false
	expenseTax.value = {}
	editingIdx.value = null
}

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

		return data
			.map((field) => {
				if (field.fieldname === "account_head") {
					field.linkFilters = {
						company: props.expenseClaim.company,
						account_type: [
							"in",
							[
								"Tax",
								"Chargeable",
								"Income Account",
								"Expenses Included In Valuation",
							],
						],
					}
				}
				return field
			})
			.filter((field) => !excludeFields.includes(field.fieldname))
	},
})
taxesTableFields.reload()

const modalTitle = computed(() => {
	if (props.isReadOnly) return "Expense Tax"

	return editingIdx.value === null ? "New Expense Tax" : "Edit Expense Tax"
})

const addButtonDisabled = computed(() => {
	return taxesTableFields.data?.some((field) => {
		if (field.reqd && !expenseTax.value[field.fieldname]) {
			return true
		}
	})
})

// child table scripts
watch(
	() => expenseTax.value.account_head,
	(value) => {
		// set description from account head
		expenseTax.value.description = value?.split(" - ").slice(0, -1).join(" - ")
	}
)

watch(
	() => expenseTax.value.rate,
	(newVal, oldVal) => {
		if (editingIdx.value && newVal && !oldVal) return

		expenseTax.value.tax_amount =
			parseFloat(props.expenseClaim.total_sanctioned_amount) *
			(parseFloat(newVal) / 100)
		calculateTotalTax()
	}
)

watch(
	() => expenseTax.value.tax_amount,
	(_value) => {
		calculateTotalTax()
	}
)

function calculateTotalTax() {
	expenseTax.value.total =
		parseFloat(props.expenseClaim.total_sanctioned_amount) +
		parseFloat(expenseTax.value.tax_amount)
}
</script>
