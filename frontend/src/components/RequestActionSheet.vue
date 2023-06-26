<template>
	<div class="bg-white w-full flex flex-col items-center justify-center pb-5">
		<div class="w-full pt-8 pb-5 border-b text-center">
			<span class="text-gray-900 font-bold text-xl">{{ data.doctype }}</span>
		</div>
		<div class="w-full flex flex-col items-center justify-center gap-5 p-4">
			<!-- Request Summary -->
			<div
				v-for="field in fieldsWithValues"
				:key="field.fieldname"
				:class="[
					['Small Text', 'Text', 'Long Text'].includes(field.fieldtype)
						? 'flex-col'
						: 'flex-row items-center justify-between',
					'flex w-full',
				]"
			>
				<div class="text-gray-600 text-base">{{ field.label }}</div>
				<FormattedField
					:value="data[field.fieldname]"
					:fieldtype="field.fieldtype"
					:fieldname="field.fieldname"
				/>
			</div>

			<!-- Actions -->
			<div
				v-if="['Open', 'Draft'].includes(document?.doc?.status)"
				class="flex w-full flex-row items-center justify-between gap-3"
			>
				<Button
					@click="updateDocumentStatus('Rejected')"
					class="w-full py-3 px-12 bg-red-100 text-red-600"
					icon-left="x"
				>
					Reject
				</Button>
				<Button
					@click="updateDocumentStatus('Approved')"
					class="w-full bg-green-600 text-white py-3 px-12"
					icon-left="check"
				>
					Approve
				</Button>
			</div>
			<div
				v-else-if="document?.doc?.docstatus === 1"
				class="flex w-full flex-row items-center justify-between gap-3"
			>
				<Button
					@click="updateDocumentStatus('Cancelled', 2)"
					class="w-full py-3 px-12 bg-red-100 text-red-600"
					icon-left="x"
				>
					Cancel
				</Button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue"
import { modalController } from "@ionic/vue"
import { toast, createDocumentResource } from "frappe-ui"

import FormattedField from "@/components/FormattedField.vue"

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

const fieldsWithValues = computed(() => {
	return props.fields.filter((field) => {
		return props.data[field.fieldname]
	})
})

const document = createDocumentResource({
	doctype: props.data.doctype,
	name: props.data.name,
})

document.reload()

const updateDocumentStatus = (status, docstatus = 1) => {
	document.setValue.submit(
		{ status: status, docstatus: docstatus },
		{
			onSuccess() {
				modalController.dismiss()
				toast({
					title: "Success",
					text: `${status} successful!`,
					icon: "check-circle",
					position: "bottom-center",
					iconClasses: "text-green-500",
				})
			},
			onError() {
				toast({
					title: "Error",
					text: `${status} failed!`,
					icon: "alert-circle",
					position: "bottom-center",
					iconClasses: "text-red-500",
				})
			},
		}
	)
}
</script>
