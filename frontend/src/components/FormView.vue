<template>
	<div class="flex flex-col h-screen w-screen" v-if="isFormReady">
		<div class="w-full sm:w-96">
			<header
				class="flex flex-row gap-1 bg-white shadow-sm py-4 px-2 items-center border-b sticky top-0 z-10"
			>
				<Button appearance="minimal" class="!px-0 !py-0" @click="router.back()">
					<FeatherIcon name="chevron-left" class="h-5 w-5" />
				</Button>
				<div v-if="id" class="flex flex-row items-center gap-2">
					<h2 class="text-2xl font-semibold text-gray-900">
						{{ doctype }}
					</h2>
					<Badge :label="id" color="white" />
				</div>
				<h2 v-else class="text-2xl font-semibold text-gray-900">
					{{ `New ${doctype}` }}
				</h2>
			</header>

			<div class="flex flex-col space-y-4 bg-white p-4">
				<FormField
					v-for="field in props.fields"
					:key="field.name"
					:fieldtype="field.fieldtype"
					:fieldname="field.fieldname"
					v-model="formModel[field.fieldname]"
					:default="field.default"
					:label="field.label"
					:options="field.options"
					:documentList="field.documentList"
					:readOnly="Boolean(field.read_only)"
					:reqd="Boolean(field.reqd)"
					:hidden="Boolean(field.hidden)"
					:errorMessage="field.error_message"
					:minDate="field.minDate"
					:maxDate="field.maxDate"
				/>
			</div>

			<div class="p-4 bg-white">
				<ErrorMessage
					class="mb-2"
					:message="docList.insert.error || documentResource?.setValue?.error"
				/>
				<Button
					class="w-full rounded-md py-2.5 px-3.5"
					appearance="primary"
					@click="submitForm"
					:disabled="saveButtonDisabled"
					:loading="
						docList.insert.loading || documentResource?.setValue?.loading
					"
				>
					Save
				</Button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, onMounted } from "vue"
import { useRouter } from "vue-router"
import {
	ErrorMessage,
	Badge,
	FeatherIcon,
	createListResource,
	createDocumentResource,
	toast,
} from "frappe-ui"
import FormField from "@/components/FormField.vue"

const props = defineProps({
	doctype: {
		type: String,
		required: true,
	},
	modelValue: {
		type: Object,
		required: true,
	},
	fields: {
		type: Array,
		required: true,
	},
	id: {
		type: String,
		required: false,
	},
})
const router = useRouter()
const emit = defineEmits(["validateForm", "update:modelValue"])

const formModel = computed({
	get() {
		return props.modelValue
	},
	set(newValue) {
		emit("update:modelValue", newValue)
	},
})

const docList = createListResource({
	doctype: props.doctype,
	insert: {
		onSuccess() {
			toast({
				title: "Success",
				text: `${props.doctype} created successfully!`,
				icon: "check-circle",
				position: "bottom-center",
				iconClasses: "text-green-500",
			})
			router.back()
		},
		onError() {
			console.log(`Error creating ${props.doctype}`)
		},
	},
})

const documentResource = createDocumentResource({
	doctype: props.doctype,
	name: props.id,
	fields: "*",
	setValue: {
		onSuccess() {
			toast({
				title: "Success",
				text: `${props.doctype} updated successfully!`,
				icon: "check-circle",
				position: "bottom-center",
				iconClasses: "text-green-500",
			})
			router.back()
		},
		onError() {
			console.log(`Error updating ${props.doctype}`)
		},
	},
})

const saveButtonDisabled = computed(() => {
	return props.fields?.some((field) => {
		if (field.reqd && !formModel.value[field.fieldname]) {
			return true
		}
	})
})

function handleDocInsert() {
	docList.insert.submit(formModel.value)
}

async function handleDocUpdate() {
	if (documentResource.doc) {
		await documentResource.setValue.submit(formModel.value)
		await documentResource.get.promise
		formModel.value = documentResource.doc
	}
}

function submitForm() {
	emit("validateForm")

	if (props.id) {
		handleDocUpdate()
	} else {
		handleDocInsert()
	}
}

const isFormReady = computed(() => {
	if (!props.id) return true

	return !documentResource.get.loading && documentResource.doc
})

onMounted(async () => {
	if (props.id) {
		await documentResource.get.promise
		formModel.value = documentResource.doc
	}
})
</script>
