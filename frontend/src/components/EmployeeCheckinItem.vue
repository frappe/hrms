<template>
	<ListItem>
		<template #left>
			<span class="lucide-clock h-5 w-5 text-gray-500" />
			<div class="flex flex-col items-start gap-1.5">
				<div class="text-base text-gray-800">Log Type: {{ props.doc.log_type }}</div>
				<div class="text-xs text-gray-500">
					<span>{{ formatTimestamp(props.doc.time) }}</span>
				</div>
			</div>
		</template>
		<template #right>
			<span class="lucide-chevron-right h-5 w-5 text-gray-500" />
		</template>
	</ListItem>
</template>

<script setup>

import ListItem from "@/components/ListItem.vue"
import { formatTimestamp } from "@/utils/formatters"

const props = defineProps({
	doc: {
		type: Object,
	},
})
</script>
