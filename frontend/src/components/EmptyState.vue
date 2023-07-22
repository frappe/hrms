<template>
	<div class="text-sm text-gray-500 mt-5 flex flex-col items-center">
		{{ props.message }}
	</div>
</template>

<script setup>
const props = defineProps({
	message: {type: String}
})
</script>