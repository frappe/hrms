<template>
	<div class="flex p-1 bg-gray-200 rounded-lg">
		<button
			v-for="button in buttons"
			:key="button.label"
			class="px-8 py-2.5 transition-all rounded-md flex-auto font-medium text-base"
			:class="
				modelValue === button.label
					? 'bg-white shadow text-gray-900'
					: 'text-gray-600'
			"
			@click="$emit('update:modelValue', button.label)"
		>
			{{ button.label }}
		</button>
	</div>
</template>

<script setup>
const props = defineProps({
	buttons: {
		type: Array,
		required: true,
	},
	modelValue: {
		type: String,
	},
})

defineEmits(["update:modelValue"])
</script>
