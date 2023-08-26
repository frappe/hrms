<template>
	<div class="flex flex-col gap-3 py-4">
		<label class="file-select">
			<h2 class="text-lg font-semibold text-gray-800 pb-4">Attachments</h2>
			<div class="select-button cursor-pointer">
				<div
					class="flex flex-col w-full border shadow-sm items-center rounded-lg p-3 gap-2"
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
					accept="*"
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
						<a target="_blank" :href="file.file_url">
							<span class="grow">{{ file.file_name || file.name }}</span>
						</a>
						<FeatherIcon
							name="x"
							class="h-3 w-3 cursor-pointer text-gray-700"
							@click="() => confirmDeleteAttachment(file)"
						/>
					</div>
				</li>
			</ul>

			<Dialog
				:options="{
					title: 'Delete Attachment',
					message: `Are you sure you want to delete the attachment ${deleteAttachment.file_name}?`,
					icon: {
						name: 'trash',
						appearance: 'danger',
					},
					size: 'xs',
					actions: [
						{
							label: 'Delete',
							appearance: 'danger',
							handler: ({ close }) => {
								emit('handle-file-delete', deleteAttachment)
								close() // closes dialog
							},
						},
						{ label: 'Cancel' },
					],
				}"
				v-model="showDialog"
			/>
		</div>
	</div>
</template>

<script setup>
import { FeatherIcon, Dialog } from "frappe-ui"
import { ref } from "vue"

const props = defineProps({
	modelValue: {
		type: Object,
		required: true,
	},
})
let showDialog = ref(false)
let deleteAttachment = ref({})

const emit = defineEmits(["handle-file-select", "handle-file-delete"])

function confirmDeleteAttachment(fileObj) {
	deleteAttachment.value = fileObj
	showDialog.value = true
}
</script>
