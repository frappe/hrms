<template>
	<div class="flex flex-row justify-between items-center">
		<h2 class="text-base-semibold text-gray-800">
			{{ __("Settle against Advances") }}
		</h2>
	</div>

	<div class="flex flex-col gap-2.5" v-if="expenseClaim.advances?.length">
		<!-- Advance Card -->
		<div
			v-for="advance in expenseClaim.advances"
			:key="advance.name"
			class="flex flex-col bg-white border shadow-sm rounded p-3.5"
			:class="[
				advance.selected ? 'border-gray-500' : '',
				isReadOnly ? '' : 'cursor-pointer',
			]"
			@click="toggleAdvanceSelection(advance)"
		>
			<div class="flex flex-row justify-between items-center">
				<div class="flex flex-row items-start gap-3">
					<FormControl
						type="checkbox"
						class="mt-[1.5px]"
						v-model="advance.selected"
						:disabled="isReadOnly"
					/>

					<div class="flex flex-col items-start gap-1.5">
						<div class="text-base-semibold text-gray-800">
							{{ advance.purpose || advance.employee_advance }}
						</div>
						<div class="flex flex-row items-center gap-3 justify-between">
							<div class="text-xs text-gray-500">
								{{ __("{0}: {1}", [
									__("Unclaimed Amount"),
									formatCurrency(advance.unclaimed_amount, expenseClaim.currency),
								]) }}
							</div>
						</div>
					</div>
				</div>

				<div class="flex flex-row items-center gap-2">
					<span class="text-normal">
						{{ currencySymbol }}
					</span>
					<TextInput
						type="number"
						class="w-20"
						v-model="advance.allocated_amount"
						@update:model-value="(v) => (advance.selected = Boolean(v))"
						@click.stop
						:disabled="isReadOnly"
						:max="advance.unclaimed_amount"
						min="0"
					/>
				</div>
			</div>
		</div>
	</div>

	<EmptyState v-else :message="__('No advances found')" :isTableField="true" />
</template>

<script setup>
import { computed, inject } from "vue"
import { TextInput } from "frappe-ui"
import { getCurrencySymbol } from "@/data/currencies"
import { formatCurrency } from "@/utils/formatters"

const __ = inject("$translate")
const props = defineProps({
	expenseClaim: {
		type: Object,
		required: true,
	},
	isReadOnly: {
		type: Boolean,
		default: false,
	},
})

const currencySymbol = computed(() => getCurrencySymbol(props.expenseClaim.currency))

function toggleAdvanceSelection(advance) {
	if (props.isReadOnly) return
	advance.selected = !advance.selected
}
</script>
