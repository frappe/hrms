<template>
	<div
		class="flex flex-col items-center rounded p-5 text-sm text-gray-600"
		:class="[
			props.isTableField ? 'border-2 border-dashed border-gray-300 mt-5' : '',
		]"
	>
		{{ __(props.message) }}
	</div>
</template>

<script setup>
const props = defineProps({
	message: { type: String },
	isTableField: { type: Boolean, default: false },
})
</script>
