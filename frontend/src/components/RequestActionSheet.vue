<template>
	<div class="w-full flex flex-col items-center justify-center mb-5">
		<div class="w-full pt-8 pb-5 border-b text-center">
			<span class="text-gray-900 font-bold text-xl">{{ data.doctype }}</span>
		</div>
		<div class="w-full flex flex-col items-center justify-center gap-5 p-4">
			<div
				v-for="field in fieldsWithValues"
				:key="field.fieldname"
				class="flex flex-row items-center justify-between w-full"
			>
				<div class="text-gray-600 text-base">{{ field.label }}</div>
				<FormattedField
					:value="data[field.fieldname]"
					:fieldtype="field.fieldtype"
					:fieldname="field.fieldname"
				/>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue"
import FormattedField from "@/components/FormattedField.vue"

const props = defineProps({
	fields: {
		type: Array,
		required: true,
	},
	data: {
		type: Object,
		required: true,
	},
})

const fieldsWithValues = computed(() => {
	return props.fields.filter((field) => {
		return props.data[field.fieldname]
	})
})

</script>
