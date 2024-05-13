<template>
	<!-- Filter Action Sheet -->
	<div class="bg-white w-full flex flex-col items-center justify-center pb-5 max-h-[calc(100vh-5rem)]">
		<div class="w-full pt-8 pb-5 border-b text-center sticky top-0 z-[100]">
			<span class="text-gray-900 font-bold text-lg">Sort Fields</span>
		</div>
		<div class="w-full p-4 overflow-auto">
			<div class="flex flex-col gap-5 items-center justify-center">
				<div v-for="field in sortFields" :key="field" class="flex flex-col w-full gap-1">
					<!-- Sort Field -->
					<div class="flex flex-col gap-2">
						<Button variant="outline" @click="setSortOrder(field)" class="text-sm text-gray-800">
							{{ field }}
						</Button>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue"

const props = defineProps({
	sortFields: {
		type: Object,
		required: true,
	},
	sortOrder: {
		type: Object,
		required: true,
	},
})

const emit = defineEmits(["update:sortOrder"])

const sortOrder = computed({
	get() {
		return props.sortOrder
	},
	set(value) {
		emit("update:sortOrder", value)
	},
})

function setSortOrder(field) {
	sortOrder.value.field = field
	sortOrder.value.order = "asc"
}
</script>
