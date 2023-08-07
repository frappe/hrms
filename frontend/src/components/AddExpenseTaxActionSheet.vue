<template>
	<!-- Add Expense Tax Action Sheet -->
	<div class="bg-white w-full flex flex-col items-center justify-center pb-5">
		<div class="w-full pt-8 pb-5 border-b text-center">
			<span class="text-gray-900 font-bold text-xl">Add Expense Tax</span>
		</div>
		<div class="w-full flex flex-col items-center justify-center gap-5 p-4">
			<div class="flex flex-col w-full space-y-4">
				<FormField
					v-for="field in fields"
					:key="field.fieldname"
					class="w-full"
					:label="field.label"
					:fieldtype="field.fieldtype"
					:fieldname="field.fieldname"
					:options="field.options"
					:hidden="field.hidden"
					:reqd="field.reqd"
					:readOnly="field.read_only"
					:default="field.default"
					v-model="expenseTax[field.fieldname]"
				/>
			</div>

			<div class="flex w-full flex-row items-center justify-between gap-3">
				<Button
					appearance="primary"
					class="w-full py-3 px-12"
					@click="emit('add-expense-tax', expenseTax)"
					:disabled="addButtonDisabled"
				>
					Add Tax
				</Button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, ref, watch } from "vue"
import FormField from "@/components/FormField.vue"

const props = defineProps({
	fields: {
		type: Array,
		required: true,
	},
	totalSanctionedAmount: {
		type: Number,
		required: true,
	},
})
const emit = defineEmits(["add-expense-tax"])

const expenseTax = ref({})

const addButtonDisabled = computed(() => {
	return props.fields?.some((field) => {
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
		expenseTax.value.description = value.split(" - ").slice(0, -1).join(" - ")
	}
)

watch(
	() => expenseTax.value.rate,
	(value) => {
		expenseTax.value.tax_amount =
			parseFloat(props.totalSanctionedAmount) * (parseFloat(value) / 100)
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
		parseFloat(props.totalSanctionedAmount) +
		parseFloat(expenseTax.value.tax_amount)
}
</script>
