<template>
	<div class="flex flex-col h-full w-full" v-if="isFormReady">
		<div
			class="w-full h-full bg-white sm:w-96 flex flex-col relative overflow-y-auto"
		>
			<header
				class="flex flex-row gap-1 bg-white shadow-sm py-4 px-2 items-center border-b sticky top-0 z-[1000]"
			>
				<Button appearance="minimal" class="!px-0 !py-0" @click="router.back()">
					<FeatherIcon name="chevron-left" class="h-5 w-5" />
				</Button>
				<div v-if="id" class="flex flex-row items-center gap-2 overflow-hidden">
					<h2
						class="text-2xl font-semibold text-gray-900 whitespace-nowrap overflow-hidden text-ellipsis"
					>
						{{ doctype }}
					</h2>
					<Badge :label="id" color="white" class="whitespace-nowrap" />
					<Badge
						v-if="formModel.status"
						:label="formModel.status"
						:color="statusColor"
						class="whitespace-nowrap"
					/>
				</div>
				<h2 v-else class="text-2xl font-semibold text-gray-900">
					{{ `New ${doctype}` }}
				</h2>
			</header>

			<!-- Form -->
			<div class="bg-white grow">
				<!-- Tabs -->
				<div
					class="px-4 sticky top-14 z-[100] bg-white text-sm font-medium text-center text-gray-500 border-b border-gray-200 dark:text-gray-400 dark:border-gray-700"
				>
					<ul class="flex flex-wrap -mb-px">
						<li class="mr-2" v-for="tab in tabs">
							<button
								@click="activeTab = tab.name"
								class="inline-block p-4 border-b-2 border-transparent rounded-t-lg"
								:class="[
									activeTab === tab.name
										? '!text-blue-600 !border-blue-600'
										: 'hover:text-gray-600 hover:border-gray-300',
								]"
							>
								{{ tab.name }}
							</button>
						</li>
					</ul>
				</div>

				<template
					v-if="tabbedView"
					v-for="(fieldList, tabName, index) in tabFields"
				>
					<div
						v-show="tabName === activeTab"
						class="flex flex-col space-y-4 p-4"
					>
						<template v-for="field in fieldList" :key="field.fieldname">
							<slot
								v-if="field.fieldtype == 'Table'"
								:name="field.fieldname"
							></slot>

							<FormField
								v-else
								:fieldtype="field.fieldtype"
								:fieldname="field.fieldname"
								v-model="formModel[field.fieldname]"
								:default="field.default"
								:label="field.label"
								:options="field.options"
								:linkFilters="field.linkFilters"
								:documentList="field.documentList"
								:readOnly="Boolean(field.read_only)"
								:reqd="Boolean(field.reqd)"
								:hidden="Boolean(field.hidden)"
								:errorMessage="field.error_message"
								:minDate="field.minDate"
								:maxDate="field.maxDate"
								:addSectionPadding="fieldList[0].name !== field.name"
							/>
						</template>

						<FileUploaderView
							v-if="showAttachmentView && index === 0"
							v-model="fileAttachments"
							@handleFileSelect="handleFileSelect"
							@handleFileDelete="handleFileDelete"
						/>
					</div>
				</template>

				<div class="flex flex-col space-y-4 p-4" v-else>
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

					<FileUploaderView
						v-if="showAttachmentView"
						v-model="fileAttachments"
						@handleFileSelect="handleFileSelect"
						@handleFileDelete="handleFileDelete"
					/>
				</div>
			</div>

			<!-- Bottom Save Button -->
			<div
				class="px-4 pt-4 mt-2 sm:w-96 bg-white sticky bottom-0 w-full drop-shadow-xl z-40 border-t rounded-t-xl pb-10"
			>
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
import { computed, onMounted, ref } from "vue"
import { useRouter } from "vue-router"
import {
	ErrorMessage,
	Badge,
	FeatherIcon,
	createListResource,
	createDocumentResource,
	toast,
	createResource,
} from "frappe-ui"
import FormField from "@/components/FormField.vue"
import FileUploaderView from "@/components/FileUploaderView.vue"

import { FileAttachment, guessStatusColor } from "@/composables/index"

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
	tabbedView: {
		type: Boolean,
		required: false,
		default: false,
	},
	tabs: {
		type: Array,
		required: false,
	},
	showAttachmentView: {
		type: Boolean,
		required: false,
		default: false,
	},
})
const emit = defineEmits(["validateForm", "update:modelValue"])
const router = useRouter()
let activeTab = ref(props.tabs?.[0].name)
let fileAttachments = ref([])
let statusColor = ref("")

const formModel = computed({
	get() {
		return props.modelValue
	},
	set(newValue) {
		emit("update:modelValue", newValue)
	},
})

const tabFields = computed(() => {
	let fieldsByTab = {}
	let fieldList = []
	let firstFieldIndex = 0
	let lastFieldIndex = 0

	props.tabs?.forEach((tab) => {
		lastFieldIndex = props.fields.findIndex(
			(field) => field.fieldname === tab.lastField
		)
		fieldList = props.fields.slice(firstFieldIndex, lastFieldIndex + 1)
		fieldsByTab[tab.name] = fieldList
		firstFieldIndex = lastFieldIndex + 1
	})

	return fieldsByTab
})

const attachedFiles = createResource({
	url: "hrms.api.get_attachments",
	params: {
		dt: props.doctype,
		dn: props.id,
	},
	transform(data) {
		return data.map((file) => (file.uploaded = true))
	},
	onSuccess(data) {
		fileAttachments.value = data
	},
})

const handleFileSelect = (e) => {
	fileAttachments.value.push(...e.target.files)

	if (props.id) {
		uploadAllAttachments(props.doctype, props.id)
	}
}

const handleFileDelete = async (fileObj) => {
	if (fileObj.uploaded) {
		const fileAttachment = new FileAttachment(fileObj)
		await fileAttachment.delete()
		await attachedFiles.reload()
	} else {
		fileAttachments.value = fileAttachments.value.filter(
			(file) => file.name !== fileName
		)
	}
}

const uploadAttachment = async (doctype, name, file) => {
	const fileAttachment = new FileAttachment(file)
	return fileAttachment.upload(doctype, name).promise
}

async function uploadAllAttachments(documentType, documentName) {
	for (const attachment of fileAttachments.value) {
		if (!attachment.uploaded) {
			await uploadAttachment(documentType, documentName, attachment)
			attachment.uploaded = true
		}
	}
}

// create/update doc
const docList = createListResource({
	doctype: props.doctype,
	insert: {
		async onSuccess(data) {
			toast({
				title: "Success",
				text: `${props.doctype} created successfully!`,
				icon: "check-circle",
				position: "bottom-center",
				iconClasses: "text-green-500",
			})

			await uploadAllAttachments(data.doctype, data.name)
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

async function setStatusColor() {
	const status = formModel.value.status || formModel.value.approval_status
	if (status) {
		statusColor.value = await guessStatusColor(props.doctype, status)
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
		await attachedFiles.reload()
		await setStatusColor()
	}
})
</script>
