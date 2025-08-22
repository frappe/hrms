<template>
	<!-- Header -->
	<div class="flex flex-row justify-between items-center mt-2">
		<h2 class="text-base font-semibold text-gray-800">{{ __("Expenses") }} </h2>
		<div class="flex flex-row gap-3 items-center">
			<span class="text-base font-semibold text-gray-800">
				{{ formatCurrency(expenseClaim.total_claimed_amount, currency) }}
			</span>
			<Button
				v-if="!isReadOnly"
				id="add-expense-modal"
				class="text-sm"
				icon="plus"
				variant="subtle"
				@click="openModal()"
			/>
		</div>
	</div>

	<!-- Table -->
	<div
		v-if="expenseClaim.expenses"
		class="flex flex-col bg-white mt-5 rounded border overflow-auto"
	>
		<div
			class="flex flex-row p-3.5 items-center justify-between border-b cursor-pointer"
			v-for="(item, idx) in expenseClaim.expenses"
			:key="idx"
			@click="openModal(item, idx)"
		>
			<div class="flex flex-col w-full justify-center gap-2.5">
				<div class="flex flex-row items-center justify-between">
					<div class="flex flex-row items-start gap-3 grow">
						<div class="flex flex-col items-start gap-1.5">
							<div class="text-base font-normal text-gray-800">
								{{ __(item.expense_type) }}
							</div>
							<div class="text-xs font-normal text-gray-500">
								<span>
									{{
										__("{0}: {1}", [
											__("Sanctioned"),
											formatCurrency(item.sanctioned_amount || 0, currency),
										])
									}}
								</span>
								<span class="whitespace-pre"> &middot; </span>
								<span class="whitespace-nowrap" v-if="item.expense_date">
									{{ dayjs(item.expense_date).format("D MMM") }}
								</span>
							</div>
						</div>
					</div>
					<div class="flex flex-row justify-end items-center gap-2">
						<span class="text-gray-700 font-normal rounded text-base">
							{{ formatCurrency(item.amount, currency) }}
						</span>
						<FeatherIcon name="chevron-right" class="h-5 w-5 text-gray-500" />
					</div>
				</div>
			</div>
		</div>
	</div>
	<EmptyState v-else :message="__('No expenses added')" :isTableField="true" />

	<CustomIonModal :isOpen="isModalOpen" @didDismiss="resetSelectedItem()">
		<template #actionSheet>
			<!-- Add Expense Action Sheet -->
			<div
				class="bg-white w-full flex flex-col items-center justify-center pb-5"
			>
				<div class="w-full pt-8 pb-5 border-b text-center">
					<span class="text-gray-900 font-bold text-lg">
						{{ modalTitle }}
					</span>
				</div>
				<div class="w-full flex flex-col items-center justify-center gap-5 p-4 max-h-[80vh]">
					<div class="flex flex-col w-full space-y-4 overflow-y-auto">
						<FormField
							v-for="field in expensesTableFields.data"
							:key="field.fieldname"
							class="w-full"
							:label="__(field.label, null, 'Expense Claim Detail')"
							:fieldtype="field.fieldtype"
							:fieldname="field.fieldname"
							:options="field.options"
							:hidden="field.hidden"
							:reqd="field.reqd"
							:default="field.default"
							:readOnly="field.read_only || isReadOnly"
							v-model="expenseItem[field.fieldname]"
						/>
					</div>

					<div
						v-if="!isReadOnly"
						class="flex w-full flex-row items-center justify-between gap-3"
					>
						<Button
							v-if="editingIdx !== null"
							class="border-red-600 text-red-600 py-5 text-sm"
							variant="outline"
							theme="red"
							@click="deleteExpenseItem()"
						>
							<template #prefix>
								<FeatherIcon name="trash" class="w-4" />
							</template>
							{{ __("Delete") }}
						</Button>
						<Button
							variant="solid"
							class="w-full py-5 text-sm disabled:bg-gray-700 disabled:text-white"
							@click="updateExpenseItem()"
							:disabled="addButtonDisabled"
						>
							<template #prefix>
								<FeatherIcon
									:name="editingIdx === null ? 'plus' : 'check'"
									class="w-4"
								/>
							</template>
							{{ editingIdx === null ? __("Add Expense") : __("Update Expense") }}
						</Button>
					</div>
				</div>
			</div>
		</template>
	</CustomIonModal>
</template>

<script setup>
import { FeatherIcon, createResource } from "frappe-ui"
import { computed, ref, watch, inject } from "vue"

import FormField from "@/components/FormField.vue"
import EmptyState from "@/components/EmptyState.vue"
import CustomIonModal from "@/components/CustomIonModal.vue"

import { claimTypesByID } from "@/data/claims"
import { formatCurrency } from "@/utils/formatters"

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
	"add-expense-item",
	"update-expense-item",
	"delete-expense-item",
])
const dayjs = inject("$dayjs")
const __ = inject("$translate")
const expenseItem = ref({})
const editingIdx = ref(null)

const isModalOpen = ref(false)
const isFirstRender = ref(false)

const openModal = async (item, idx) => {
	if (item) {
		expenseItem.value = { ...item }
		editingIdx.value = idx
	}
	isFirstRender.value = true
	isModalOpen.value = true
}

const deleteExpenseItem = () => {
	emit("delete-expense-item", editingIdx.value)
	resetSelectedItem()
}

const updateExpenseItem = () => {
	if (editingIdx.value === null) {
		emit("add-expense-item", expenseItem.value)
	} else {
		emit("update-expense-item", expenseItem.value, editingIdx.value)
	}
	resetSelectedItem()
}

function resetSelectedItem() {
	isFirstRender.value = false
	isModalOpen.value = false
	expenseItem.value = {}
	editingIdx.value = null
}

const expensesTableFields = createResource({
	url: "hrms.api.get_doctype_fields",
	params: { doctype: "Expense Claim Detail" },
	transform(data) {
		const excludeFields = ["description_sb", "amounts_sb"]
		return data.filter((field) => !excludeFields.includes(field.fieldname))
	},
})
expensesTableFields.reload()

const modalTitle = computed(() => {
	if (props.isReadOnly) return __("Expense Item")

	return editingIdx.value === null ? __("New Expense Item") : __("Edit Expense Item")
})

const addButtonDisabled = computed(() => {
	return expensesTableFields.data?.some((field) => {
		if (field.reqd && !expenseItem.value[field.fieldname]) {
			return true
		}
	})
})

// child table form scripts
watch(
	() => expenseItem.value.expense_type,
	(value) => {
		if (!expenseItem.value.description) {
			expenseItem.value.description = claimTypesByID[value]?.description
		}

		expenseItem.value.cost_center = props.expenseClaim.cost_center
	}
)

watch(
	() => expenseItem.value.amount,
	(value) => {
		if (!isFirstRender.value) {
			expenseItem.value.sanctioned_amount = parseFloat(value)
		} else {
			isFirstRender.value = false
		}
	}
)
</script>
