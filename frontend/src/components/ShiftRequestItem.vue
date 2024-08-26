<template>
	<div class="flex flex-col w-full justify-center gap-2.5">
		<div class="flex flex-row items-center justify-between">
			<div class="flex flex-row items-start gap-3 grow">
				<FeatherIcon name="clock" class="h-5 w-5 text-gray-500" />
				<div class="flex flex-col items-start gap-1.5">
					<div class="text-base font-normal text-gray-800">
						{{ props.doc.shift_type }}
					</div>
					<div class="text-xs font-normal text-gray-500">
						<span>{{ props.doc.shift_dates || getShiftRequestDates(props.doc) }}</span>
						<span v-if="props.doc.to_date">
							<span class="whitespace-pre"> &middot; </span>
							<span class="whitespace-nowrap">{{
								`${props.doc.total_shift_days || getTotalShiftRequestDays(props.doc)}d`
							}}</span>
						</span>
					</div>
				</div>
			</div>
			<div class="flex flex-row justify-end items-center gap-2">
				<Badge variant="outline" :theme="colorMap[status]" :label="status" size="md" />
				<FeatherIcon name="chevron-right" class="h-5 w-5 text-gray-500" />
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue"
import { Badge, FeatherIcon } from "frappe-ui"

import { getShiftRequestDates, getTotalShiftRequestDays } from "@/data/attendance"

const props = defineProps({
	doc: {
		type: Object,
	},
})

const status = computed(() => {
	return props.doc.docstatus ? props.doc.status : "Open"
})

const colorMap = {
	Approved: "green",
	Rejected: "red",
	Open: "orange",
}
</script>
