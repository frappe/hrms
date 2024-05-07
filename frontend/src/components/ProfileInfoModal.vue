<template>
	<div
		class="bg-white w-full flex flex-col items-center justify-center pb-5 max-h-[calc(100vh-5rem)]"
	>
		<!-- Header -->
		<div
			class="w-full flex flex-row gap-2 pt-8 pb-5 border-b justify-center items-center sticky top-0 z-[100]"
		>
			<span class="text-gray-900 font-bold text-lg text-center">
				{{ title }}
			</span>
		</div>

		<div class="w-full flex flex-col items-center justify-center gap-4 p-4">
			<div
				v-for="item in data"
				:key="item.fieldname"
				class="flex flex-row items-center justify-between w-full"
			>
				<div class="text-gray-600 text-base">{{ item.label }}</div>
				<FormattedField
					:value="item.value"
					:fieldtype="item.fieldtype"
					:fieldname="item.fieldname"
				/>
			</div>
		</div>
	</div>
</template>

<script setup>
import { FeatherIcon } from "frappe-ui"
import FormattedField from "@/components/FormattedField.vue"

const props = defineProps({
	title: {
		type: String,
		required: true,
	},
	data: {
		type: Array,
		required: true,
	},
})
</script>
