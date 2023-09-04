<template>
	<div
		class="text-sm text-gray-500 rounded flex flex-col items-center bg-gray-100 p-5"
	>
		{{ props.message }}
	</div>
</template>

<script setup>
const props = defineProps({
	message: { type: String },
})
</script>
