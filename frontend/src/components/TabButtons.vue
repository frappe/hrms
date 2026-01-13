<template>
	<div class="flex p-1 bg-theme-secondary-button rounded">
		<button
			v-for="button in buttons"
			:key="button.key ?? button.label ?? button"
			class="px-8 py-2.5 transition-all rounded-[7px] flex-auto font-medium text-base"
			:class="
				modelValue === (button.key ?? button.label ?? button)
					? 'bg-theme-primary-button drop-shadow text-theme-primary-button-text'
					: 'text-theme-secondary-button-text'
			"
			@click="$emit('update:modelValue', button.key ?? button.label ?? button)"
		>
			{{ button.label ?? __(button) }}
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
