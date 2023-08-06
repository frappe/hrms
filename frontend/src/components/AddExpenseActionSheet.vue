<template>
	<!-- Add Expense Action Sheet -->
	<div class="bg-white w-full flex flex-col items-center justify-center pb-5">
		<div class="w-full pt-8 pb-5 border-b text-center">
			<span class="text-gray-900 font-bold text-xl">New Expense Item</span>
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
					:default="field.default"
					v-model="expenseItem[field.fieldname]"
				/>
			</div>

			<div class="flex w-full flex-row items-center justify-between gap-3">
				<Button
					appearance="primary"
					class="w-full py-3 px-12"
					@click="emit('add-expense-item', expenseItem)"
					:disabled="addButtonDisabled"
				>
					Add Expense
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
})
const emit = defineEmits(["add-expense-item"])

const expenseItem = ref({})

const addButtonDisabled = computed(() => {
	return props.fields?.some((field) => {
		if (field.reqd && !expenseItem.value[field.fieldname]) {
			return true
		}
	})
})

watch(
	() => expenseItem.value.amount,
	(value) => {
		expenseItem.value.sanctioned_amount = parseFloat(value)
	}
)
</script>
