<template>
	<div v-if="showField" class="flex flex-col gap-1.5">
		<!-- Label -->
		<span
			v-if="
				!props.hideLabel &&
				!['Check', 'Section Break', 'Column Break'].includes(props.fieldtype)
			"
			:class="[
				// mark field as mandatory
				props.reqd ? `after:content-['_*'] after:text-red-600` : ``,
				`block text-sm leading-5 text-gray-700`,
			]"
		>
			{{ props.label }}
		</span>

		<!-- Select or Link field with predefined options -->
		<Combobox
			v-if="props.fieldtype === 'Select' || props.documentList"
			:class="isReadOnly ? 'pointer-events-none' : ''"
			:placeholder="__('Select {0}', [props.label])"
			:options="selectionList"
			:model-value="modelValue"
			v-bind="$attrs"
			:disabled="isReadOnly"
			@update:model-value="(v) => emit('update:modelValue', v)"
		/>

		<!-- Link field -->
		<Link
			v-else-if="props.fieldtype === 'Link'"
			:doctype="props.options"
			:modelValue="modelValue"
			:filters="props.linkFilters"
			:disabled="isReadOnly"
			@update:modelValue="(v) => emit('update:modelValue', v)"
		/>

		<Editor
			v-else-if="props.fieldtype === 'Text Editor'"
			:model-value="modelValue || ''"
			:extensions="editorExtensions"
			:placeholder="__('Enter {0}', [props.label])"
			:editable="!isReadOnly"
			:upload-function="uploadEditorFile"
			@update:model-value="(v) => emit('update:modelValue', v)"
		>
			<div class="overflow-hidden rounded-sm border border-gray-200">
				<EditorFixedMenu
					:items="articleToolbar"
					class="overflow-x-auto border-b border-gray-200 p-1"
				/>
				<EditorContent class="prose-sm p-1 min-h-[4rem]" />
			</div>
		</Editor>

		<!-- Text -->
		<Textarea
			v-else-if="['Small Text', 'Text', 'Long Text'].includes(props.fieldtype)"
			:model-value="modelValue"
			:placeholder="__('Enter {0}', [props.label])"
			@update:model-value="(v) => emit('update:modelValue', v)"
			v-bind="$attrs"
			:disabled="isReadOnly"
			class="h-15"
		/>

		<!-- Check -->
		<Checkbox
			v-else-if="props.fieldtype === 'Check'"
			:label="props.label"
			:model-value="Boolean(modelValue)"
			@update:model-value="(v) => emit('update:modelValue', v)"
			v-bind="$attrs"
			:disabled="isReadOnly"
			class="rounded-sm text-gray-800"
		/>

		<!-- Data field -->
		<TextInput
			v-else-if="props.fieldtype === 'Data'"
			type="text"
			:model-value="modelValue"
			@update:model-value="(v) => emit('update:modelValue', v)"
			v-bind="$attrs"
			:disabled="isReadOnly"
		/>

		<!-- Read only currency field -->
		<TextInput
			v-else-if="props.fieldtype === 'Currency' && isReadOnly"
			type="text"
			:model-value="modelValue"
			@update:model-value="(v) => emit('update:modelValue', v)"
			v-bind="$attrs"
			:disabled="isReadOnly"
		/>

		<!-- Float/Int field -->
		<TextInput
			v-else-if="isNumberType"
			type="number"
			:model-value="modelValue"
			@update:model-value="(v) => emit('update:modelValue', v)"
			v-bind="$attrs"
			:disabled="isReadOnly"
		/>

		<!-- Section Break -->
		<div
			v-else-if="props.fieldtype === 'Section Break'"
			:class="props.addSectionPadding ? 'mt-2' : ''"
		>
			<h2
				v-if="props.label"
				class="text-base-semibold text-gray-800"
				:class="props.addSectionPadding ? 'pt-4' : ''"
			>
				{{ props.label }}
			</h2>
		</div>

		<!-- Date -->
		<DatePicker
			v-else-if="props.fieldtype === 'Date'"
			:model-value="modelValue"
			:placeholder="__('Select {0}', [props.label])"
			:format="dateFormat"
			:typeable="false"
			@update:model-value="(v) => emit('update:modelValue', v)"
			v-bind="$attrs"
			:disabled="isReadOnly"
			:min="props.minDate"
			:max="props.maxDate"
		/>

		<!-- Time -->
		<TextInput
			v-else-if="props.fieldtype === 'Time'"
			type="time"
			step="60"
			:model-value="formatTimeValue(modelValue)"
			:placeholder="__('Select {0}', [props.label])"
			@update:model-value="(v) => emit('update:modelValue', normalizeTimeValue(v))"
			v-bind="$attrs"
			:disabled="isReadOnly"
		/>

		<!-- Datetime -->
		<DateTimePicker
			v-else-if="props.fieldtype === 'Datetime'"
			:model-value="modelValue"
			:placeholder="`Select ${props.label}`"
			format="DD-MM-YYYY HH:mm:ss"
			@update:model-value="(v) => emit('update:modelValue', v)"
			v-bind="$attrs"
			:disabled="isReadOnly"
		/>

		<ErrorMessage :message="props.errorMessage" />
	</div>
</template>

<script setup>
import {
	Checkbox,
	Combobox,
	DatePicker,
	DateTimePicker,
	ErrorMessage,
	Textarea,
	useFileUpload,
	TextInput,
} from "frappe-ui"
import {
	articleToolbar,
	Editor,
	EditorContent,
	EditorFixedMenu,
	RichTextKit,
} from "frappe-ui/editor"
import { computed, onMounted, inject } from "vue"

import Link from "@/components/Link.vue"

const __ = inject("$translate")

const props = defineProps({
	fieldtype: String,
	fieldname: String,
	modelValue: [String, Number, Boolean, Array, Object],
	default: [String, Number, Boolean, Array, Object],
	label: String,
	hideLabel: Boolean,
	options: [String, Array],
	linkFilters: Object,
	documentList: Array,
	readOnly: [Boolean, Number],
	reqd: [Boolean, Number],
	hidden: {
		type: [Boolean, Number],
		default: false,
	},
	errorMessage: String,
	minDate: String,
	maxDate: String,
	addSectionPadding: {
		type: Boolean,
		default: true,
	},
})

const emit = defineEmits(["update:modelValue"])
const dayjs = inject("$dayjs")
const dateFormat = (
	window.frappe?.boot?.sysdefaults?.date_format || "yyyy-mm-dd"
).toUpperCase()

const editorExtensions = [RichTextKit]
const editorFileUpload = useFileUpload()
const uploadEditorFile = (file) => editorFileUpload.upload(file, { private: true })

const showField = computed(() => {
	if (props.readOnly && !isLayoutField.value && !props.modelValue) return false

	return props.fieldtype !== "Table" && !props.hidden
})

const isNumberType = computed(() => {
	return ["Int", "Float", "Currency"].includes(props.fieldtype)
})

const isLayoutField = computed(() => {
	return ["Section Break", "Column Break"].includes(props.fieldtype)
})

const isReadOnly = computed(() => {
	return Boolean(props.readOnly)
})

function formatTimeValue(value) {
	if (!value) return ""
	return String(value).split(":").slice(0, 2).join(":")
}

function normalizeTimeValue(value) {
	if (!value) return ""
	const time = String(value).split(":")
	if (time.length === 2) return `${time[0]}:${time[1]}:00`
	return String(value).split(".")[0]
}

const selectionList = computed(() => {
	if (props.fieldtype === "Link" && props.documentList) {
		return props.documentList
	} else if (props.fieldtype == "Select" && props.options) {
		const options = props.options.split("\n")
		return options.map((option) => ({
			label: __(option),
			value: option,
		}))
	}

	return []
})

function setDefaultValue() {
	// set default values
	if (props.modelValue) return

	if (props.default) {
		if (props.fieldtype === "Check") {
			emit("update:modelValue", props.default === "1" ? true : false)
		} else if (props.fieldtype === "Date" && props.default === "Today") {
			emit("update:modelValue", dayjs().format("YYYY-MM-DD"))
		} else if (isNumberType.value) {
			emit("update:modelValue", parseFloat(props.default || 0))
		} else {
			emit("update:modelValue", props.default)
		}
	} else {
		props.fieldtype === "Check" ? emit("update:modelValue", false) : emit("update:modelValue", "")
	}
}

onMounted(() => {
	setDefaultValue()
})
</script>
