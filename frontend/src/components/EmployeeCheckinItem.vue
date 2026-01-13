<template>
	<ListItem>
		<template #left>
			<FeatherIcon name="clock" class="h-5 w-5 text-theme-content-box-text-secondary" />
			<div class="flex flex-col items-start gap-1.5">
				<div class="text-base font-normal text-theme-content-box-text">Log Type: {{ props.doc.log_type }}</div>
				<div class="text-xs font-normal text-theme-content-box-text-secondary">
					<span>{{ formatTimestamp(props.doc.time) }}</span>
				</div>
			</div>
		</template>
		<template #right>
			<FeatherIcon name="chevron-right" class="h-5 w-5 text-theme-content-box-text" />
		</template>
	</ListItem>
</template>

<script setup>
import { FeatherIcon } from "frappe-ui"

import ListItem from "@/components/ListItem.vue"
import { formatTimestamp } from "@/utils/formatters"

const props = defineProps({
	doc: {
		type: Object,
	},
})
</script>
