<template>
	<svg
		viewBox="0 0 48 24"
		preserveAspectRatio="xMidYMin slice"
		class="h-[84px] w-[84px] -mt-10"
	>
		<circle cx="24" cy="24" r="9" fill="#fff"></circle>
		<circle
			class="stroke-current text-gray-200"
			cx="24"
			cy="24"
			r="9"
			fill="transparent"
			stroke-width="4"
		></circle>
		<circle
			class="stroke-current"
			:class="colorClass"
			cx="24"
			cy="24"
			r="9"
			fill="transparent"
			stroke-width="4"
			:stroke-dasharray="circumference"
			:stroke-dashoffset="dashOffset"
		></circle>
	</svg>
</template>

<script setup>
import { computed } from "vue"

const props = defineProps({
	percentage: {
		type: Number,
		default: 0,
	},
	colorClass: {
		type: String,
		default: "text-orange-500",
	},
})

const circumference = computed(() => {
	return 2 * Math.PI * 9
})

const dashOffset = computed(() => {
	let halfCircumference = circumference.value / 2
	if (isNaN(props.percentage)) {
		return halfCircumference
	}
	let percentage = props.percentage
	if (percentage > 100) {
		percentage = 100
	}
	return halfCircumference - (percentage / 100) * halfCircumference
})
</script>
