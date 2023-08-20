<template>
	<div
		v-if="document?.doc"
		class="bg-white w-full flex flex-col items-center justify-center pb-5"
	>
		<div class="w-full pt-8 pb-5 border-b text-center">
			<span class="text-gray-900 font-bold text-xl">
				{{ document?.doctype }}
			</span>
		</div>
		<div class="w-full flex flex-col items-center justify-center gap-5 p-4">
			<!-- Request Summary -->
			<div
				v-for="field in fieldsWithValues"
				:key="field.fieldname"
				:class="[
					['Small Text', 'Text', 'Long Text', 'Table'].includes(field.fieldtype)
						? 'flex-col'
						: 'flex-row items-center justify-between',
					'flex w-full',
				]"
			>
				<div class="text-gray-600 text-base">{{ field.label }}</div>
				<component
					v-if="field.fieldtype === 'Table'"
					:is="field.component"
					:doc="document?.doc"
				/>
				<FormattedField
					v-else
					:value="field.value"
					:fieldtype="field.fieldtype"
					:fieldname="field.fieldname"
				/>
			</div>

			<!-- Attachments -->
			<div class="flex flex-col gap-2 w-full">
				<div class="text-gray-600 text-base">Attachments</div>
				<ul class="w-full flex flex-col items-center gap-2">
					<li
						class="bg-gray-100 rounded-lg p-2 w-full"
						v-for="(file, index) in attachedFiles.data"
						:key="index"
					>
						<div
							class="flex flex-row items-center justify-between text-gray-700 text-sm"
						>
							<a target="_blank" :href="file.file_url">
								<span class="grow">{{ file.file_name || file.name }}</span>
							</a>
						</div>
					</li>
				</ul>
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
import { computed, defineAsyncComponent } from "vue"
import { modalController } from "@ionic/vue"
import { toast, createDocumentResource, createResource } from "frappe-ui"

import FormattedField from "@/components/FormattedField.vue"
import { getCurrencySymbol, getCompanyCurrencySymbol } from "@/data/currencies"

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

const document = createDocumentResource({
	doctype: props.data.doctype,
	name: props.data.name,
	auto: true,
})

const attachedFiles = createResource({
	url: "hrms.api.get_attachments",
	params: {
		dt: props.data.doctype,
		dn: props.data.name,
	},
	auto: true,
})

const currency = computed(() => {
	if (document?.doc?.currency) return getCurrencySymbol(document?.doc?.currency)
	else if (document?.doc?.company)
		return getCompanyCurrencySymbol(document?.doc?.company)
})

const fieldsWithValues = computed(() => {
	return props.fields.filter((field) => {
		if (field.fieldtype === "Currency") {
			field.value = `${currency.value} ${document.doc?.[field.fieldname]}`
		} else {
			if (field.fieldtype === "Table") {
				// dynamically loading child table component as per config
				// does not work with @ alias due to vite's import analysis
				field.component = defineAsyncComponent(() =>
					import(`../components/${field.componentName}.vue`)
				)
			}
			field.value =
				props.data[field.fieldname] || document?.doc?.[field.fieldname]
		}

		return field.value
	})
})

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
