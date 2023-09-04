<template>
	<div
		v-if="document?.doc"
		class="bg-white w-full flex flex-col items-center justify-center pb-5 max-h-[calc(100vh-5rem)]"
	>
		<!-- Header -->
		<div
			class="w-full flex flex-row gap-2 pt-8 pb-5 border-b justify-center items-center sticky top-0 z-[100]"
		>
			<span class="text-gray-900 font-bold text-lg text-center">
				{{ document?.doctype }}
			</span>
			<FeatherIcon
				name="external-link"
				class="h-4 w-4 text-gray-500 cursor-pointer"
				@click="openFormView"
			/>
		</div>

		<!-- Request Summary -->
		<div class="w-full p-4 overflow-auto">
			<div class="flex flex-col items-center justify-center gap-5">
				<div
					v-for="field in fieldsWithValues"
					:key="field.fieldname"
					:class="[
						['Small Text', 'Text', 'Long Text', 'Table'].includes(
							field.fieldtype
						)
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
				<div
					class="flex flex-col gap-2 w-full"
					v-if="attachedFiles?.data?.length"
				>
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
			</div>
		</div>

		<!-- Actions -->
		<div
			v-if="['Open', 'Draft'].includes(document?.doc?.[approvalField])"
			class="flex w-full flex-row items-center justify-between gap-3 sticky bottom-0 border-t z-[100] p-4"
		>
			<Button
				@click="updateDocumentStatus({ status: 'Rejected' })"
				class="w-full bg-red-100 text-red-600 py-5 text-sm"
			>
				<template #prefix>
					<FeatherIcon name="x" class="w-4" />
				</template>
				Reject
			</Button>
			<Button
				@click="updateDocumentStatus({ status: 'Approved' })"
				class="w-full bg-green-600 text-white py-5 text-sm"
			>
				<template #prefix>
					<FeatherIcon name="check" class="w-4" />
				</template>
				Approve
			</Button>
		</div>

		<div
			v-else-if="
				document?.doc?.docstatus === 0 &&
				['Approved', 'Rejected'].includes(document?.doc?.[approvalField])
			"
			class="flex w-full flex-row items-center justify-between gap-3 sticky bottom-0 border-t z-[100] p-4"
		>
			<Button
				@click="updateDocumentStatus({ docstatus: 1 })"
				class="w-full py-5 text-sm"
				variant="solid"
			>
				Submit
			</Button>
		</div>

		<div
			v-else-if="document?.doc?.docstatus === 1"
			class="flex w-full flex-row items-center justify-between gap-3 sticky bottom-0 border-t z-[100] p-4"
		>
			<Button
				@click="updateDocumentStatus({ docstatus: 2 })"
				class="w-full py-5 text-sm bg-red-100 text-red-600"
			>
				<template #prefix>
					<FeatherIcon name="x" class="w-4" />
				</template>
				Cancel
			</Button>
		</div>
	</div>
</template>

<script setup>
import { computed, defineAsyncComponent } from "vue"
import { modalController } from "@ionic/vue"
import {
	toast,
	createDocumentResource,
	createResource,
	FeatherIcon,
} from "frappe-ui"

import FormattedField from "@/components/FormattedField.vue"
import { getCurrencySymbol, getCompanyCurrencySymbol } from "@/data/currencies"
import { useRouter } from "vue-router"

const props = defineProps({
	fields: {
		type: Array,
		required: true,
	},
	modelValue: {
		type: Object,
		required: true,
	},
})
const router = useRouter()

const document = createDocumentResource({
	doctype: props.modelValue.doctype,
	name: props.modelValue.name,
	auto: true,
})

const attachedFiles = createResource({
	url: "hrms.api.get_attachments",
	params: {
		dt: props.modelValue.doctype,
		dn: props.modelValue.name,
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
				document?.doc?.[field.fieldname] || props.modelValue[field.fieldname]
		}

		return field.value
	})
})

const approvalField = computed(() => {
	return props.modelValue.doctype === "Expense Claim"
		? "approval_status"
		: "status"
})

const getSuccessMessage = ({ status = "", docstatus = 0 }) => {
	if (status) return `${status} successfully!`
	else if (docstatus)
		return `Document ${
			docstatus === 1 ? "submitted" : "cancelled"
		} successfully!`
}

const getFailureMessage = ({ status = "", docstatus = 0 }) => {
	if (status)
		return `${status === "Approved" ? "Approval" : "Rejection"} failed!`
	else if (docstatus)
		return `Document ${docstatus === 1 ? "submission" : "cancellation"} failed!`
}

const updateDocumentStatus = ({ status = "", docstatus = 0 }) => {
	let updateValues = {}

	if (status) updateValues[approvalField.value] = status
	if (docstatus) updateValues.docstatus = docstatus

	document.setValue.submit(
		{ ...updateValues },
		{
			onSuccess() {
				if (docstatus !== 0) modalController.dismiss()

				toast({
					title: "Success",
					text: getSuccessMessage({ status, docstatus }),
					icon: "check-circle",
					position: "bottom-center",
					iconClasses: "text-green-500",
				})
			},
			onError() {
				toast({
					title: "Error",
					text: getFailureMessage({ status, docstatus }),
					icon: "alert-circle",
					position: "bottom-center",
					iconClasses: "text-red-500",
				})
			},
		}
	)
}

const openFormView = () => {
	modalController.dismiss()
	router.push({
		name: `${props.modelValue.doctype.replace(/\s+/g, "")}DetailView`,
		params: { id: props.modelValue.name },
	})
}
</script>
