<template>
	<div class="w-full flex flex-col items-center justify-center mb-5">
		<div class="w-full pt-8 pb-5 border-b text-center">
			<span class="text-gray-900 font-bold text-xl">{{ data.doctype }}</span>
		</div>
		<div class="w-full flex flex-col items-center justify-center gap-5 p-4">
			<div
				v-for="field in fields"
				:key="field.fieldname"
				class="flex flex-row items-center justify-between w-full"
			>
				<div class="text-gray-600 text-base">{{ field.label }}</div>
				<div class="text-gray-900 text-base">{{ data[field.fieldname] }}</div>
			</div>
		</div>
	</div>
</template>

<script setup>

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

</script>
