<template>
	<div class="flex flex-row justify-between items-center">
		<h2 class="text-lg font-semibold text-gray-800">Settle against Advances</h2>
	</div>

	<div class="flex flex-col gap-2.5" v-if="expenseClaim.advances?.length">
		<!-- Advance Card -->
		<div
			v-for="advance in expenseClaim.advances"
			:key="advance.name"
			class="flex flex-col bg-white border shadow-sm rounded-lg p-3.5"
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
						class="mt-[0.5px]"
						v-model="advance.selected"
						:disabled="isReadOnly"
					/>

					<div class="flex flex-col items-start gap-1.5">
						<div class="text-base font-semibold text-gray-800">
							{{ advance.purpose || advance.employee_advance }}
						</div>
						<div class="flex flex-row items-center gap-3 justify-between">
							<div class="text-xs font-normal text-gray-500">
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
					<FormControl
						type="number"
						class="w-20"
						v-model="advance.allocated_amount"
						@input="(v) => (advance.selected = v)"
						@click.stop
						:disabled="isReadOnly"
						:max="advance.unclaimed_amount"
						min="0"
					/>
				</div>
			</div>
		</div>
	</div>

	<EmptyState message="No advances found" v-else />
</template>

<script setup>
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

function toggleAdvanceSelection(advance) {
	if (props.isReadOnly) return
	advance.selected = !advance.selected
}
</script>
