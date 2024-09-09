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
						<span>{{ props.doc.shift_dates }}</span>
						<span v-if="props.doc.end_date" class="whitespace-pre"> &middot; </span>
						<span v-if="props.doc.end_date" class="whitespace-nowrap">{{
							`${props.doc.total_shift_days}d`
						}}</span>
					</div>
				</div>
			</div>
			<div class="flex flex-row justify-end items-center gap-2">
				<span class="text-gray-700 font-normal rounded text-base">
					{{ props.doc.shift_timing }}
				</span>
				<FeatherIcon name="chevron-right" class="h-5 w-5 text-gray-500" />
			</div>
		</div>
	</div>
</template>

<script setup>
import { FeatherIcon } from "frappe-ui"

const props = defineProps({
	doc: {
		type: Object,
	},
})
</script>
