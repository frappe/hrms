<template>
	<label class="file-select border-t pt-5">
		<h2 class="text-lg font-semibold text-gray-700 mb-2">Attachments</h2>
		<div class="select-button cursor-pointer">
			<div
				class="flex flex-col w-full border items-center rounded-lg p-4 gap-2"
			>
				<FeatherIcon name="upload" class="h-6 w-6 text-gray-700" />
				<span class="block text-sm font-normal leading-5 text-gray-700">
					Upload images or documents
				</span>
			</div>
			<input
				class="hidden"
				ref="input"
				type="file"
				multiple
				@change="(e) => emit('handle-file-select', e)"
			/>
		</div>
	</label>

	<div v-if="modelValue.length" class="w-full">
		<ul class="w-full flex flex-col items-center gap-2">
			<li
				class="bg-gray-100 rounded-lg p-2 w-full"
				v-for="(file, index) in modelValue"
				:key="index"
			>
				<div
					class="flex flex-row items-center justify-between text-gray-700 text-sm"
				>
					<span class="grow">{{ file.name }}</span>
					<FeatherIcon name="x" class="h-4 w-4 text-gray-700" />
				</div>
			</li>
		</ul>
	</div>
</template>

<script setup>
import { FeatherIcon } from "frappe-ui"

const props = defineProps({
	modelValue: {
		type: Object,
		required: true,
	},
})

const emit = defineEmits(["handle-file-select"])
</script>
