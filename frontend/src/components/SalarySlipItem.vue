<template>
	<ListItem>
		<template #left>
			<SalaryIcon class="h-5 w-5 text-gray-500" />
			<div class="flex flex-col items-start gap-1.5">
				<div class="text-base text-gray-800">
					{{ title }}
				</div>
				<div v-if="doc?.gross_pay" class="text-xs text-gray-500">
					<span>
						{{
							__("{0}: {1}", [
								__("Gross Pay"),
								formatCurrency(doc.gross_pay, doc.currency),
							])
						}}
					</span>
					<span class="whitespace-pre"> &middot; </span>
				</div>
			</div>
		</template>
		<template #right>
			<span v-if="doc?.net_pay" class="text-gray-700 rounded text-base">
				{{ formatCurrency(doc.net_pay, doc.currency) }}
			</span>
			<span class="lucide-chevron-right h-5 w-5 text-gray-500" />
		</template>
	</ListItem>
</template>

<script setup>
import { computed, inject } from "vue"

import ListItem from "@/components/ListItem.vue"
import SalaryIcon from "@/components/icons/SalaryIcon.vue"

import { formatCurrency } from "@/utils/formatters"

const dayjs = inject("$dayjs")

const props = defineProps({
	doc: {
		type: Object,
	},
})

const title = computed(() => {
	if (dayjs(props.doc.start_date).isSame(props.doc.end_date, "month")) {
		// monthly salary
		return dayjs(props.doc.start_date).format("MMM YYYY")
	} else {
		// quarterly, bimonthly, etc
		return `${dayjs(props.doc.start_date).format("MMM YYYY")} - ${dayjs(
			props.doc.end_date
		).format("MMM YYYY")}`
	}
})
</script>
