<template>
	<!-- Table -->
	<div
		v-if="doc?.expenses"
		class="flex flex-col bg-white mt-5 rounded border overflow-auto"
	>
		<div
			class="flex flex-row p-3.5 items-center justify-between cursor-pointer"
			v-for="(item, idx) in doc?.expenses"
			:key="idx"
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
					<span class="text-gray-700 font-normal rounded text-base">
						{{ formatCurrency(item.amount, currency) }}
					</span>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, inject } from "vue"

import { getCompanyCurrency } from "@/data/currencies"
import { formatCurrency } from "@/utils/formatters"

const props = defineProps({
	doc: {
		type: Object,
		required: true,
	},
})

const dayjs = inject("$dayjs")
const currency = computed(() => getCompanyCurrency(props.doc.company))
</script>
