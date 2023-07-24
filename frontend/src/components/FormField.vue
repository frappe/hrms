<template>
	<div
		v-if="showField"
		class="flex flex-col gap-1"
	>
		<!-- Label -->
		<span
			v-if="
				!['Check', 'Section Break', 'Column Break'].includes(props.fieldtype)
			"
			:class="[
				// mark field as mandatory
				props.reqd ? `after:content-['_*'] after:text-red-400` : ``,
				`block text-base leading-5 text-gray-700`,
			]"
		>
			{{ props.label }}
		</span>

		<!-- Link & Select -->
		<Autocomplete
			v-if="['Link', 'Select'].includes(props.fieldtype)"
			:value="modelValue"
			:placeholder="`Select ${props.options}`"
			:options="selectionList"
			@change="(v) => emit('update:modelValue', v.value)"
			v-bind="$attrs"
			:disabled="props.readOnly"
		/>

		<!-- Text -->
		<Input
			v-else-if="['Small Text', 'Text', 'Long Text'].includes(props.fieldtype)"
			type="textarea"
			:value="modelValue"
			:placeholder="`Enter ${props.label}`"
			@input="(v) => emit('update:modelValue', v)"
			@change="(v) => emit('change', v)"
			v-bind="$attrs"
			:disabled="props.readOnly"
		/>

		<!-- Check -->
		<Input
			v-else-if="props.fieldtype === 'Check'"
			type="checkbox"
			:label="props.label"
			:value="modelValue"
			@input="(v) => emit('update:modelValue', v)"
			@change="(v) => emit('change', v)"
			v-bind="$attrs"
			:disabled="props.readOnly"
		/>

		<!-- Data field -->
		<Input
			v-else-if="props.fieldtype === 'Data'"
			type="text"
			:value="modelValue"
			@input="(v) => emit('update:modelValue', v)"
			@change="(v) => emit('change', v)"
			v-bind="$attrs"
			:disabled="props.readOnly"
		/>

		<!-- Float/Int field -->
		<Input
			v-else-if="['Float', 'Int'].includes(props.fieldtype)"
			type="number"
			:value="modelValue"
			@input="(v) => emit('update:modelValue', v)"
			@change="(v) => emit('change', v)"
			v-bind="$attrs"
			:disabled="props.readOnly"
		/>

		<!-- Section Break -->
		<div v-else-if="props.fieldtype === 'Section Break'">
			<h2 v-if="props.label" class="pt-4 text-lg font-semibold text-gray-800">
				{{ props.label }}
			</h2>
		</div>

		<!-- Date -->
		<!-- FIXME: default datepicker has poor UI -->
		<Input
			v-else-if="props.fieldtype === 'Date'"
			type="date"
			v-model="date"
			:value="modelValue"
			:placeholder="`Select ${props.label}`"
			:formatValue="(val) => dayjs(val).format('DD-MM-YYYY')"
			@input="(v) => emit('update:modelValue', v)"
			@change="(v) => emit('change', v)"
			v-bind="$attrs"
			:disabled="props.readOnly"
			:min="props.minDate"
			:max="props.maxDate"
		/>

		<!-- Time -->
		<!-- Datetime -->

		<ErrorMessage :message="props.errorMessage"/>
	</div>
</template>

<script setup>
import { createResource, Autocomplete, ErrorMessage } from "frappe-ui"
import { ref, computed, onMounted, inject } from "vue"

const props = defineProps({
	fieldtype: String,
	fieldname: String,
	modelValue: [String, Number, Boolean, Array, Object],
	default: [String, Number, Boolean, Array, Object],
	label: String,
	options: [String, Array],
	documentList: Array,
	readOnly: Boolean,
	reqd: Boolean,
	hidden: {
		type: Boolean,
		default: true,
	},
	errorMessage: String,
	minDate: String,
	maxDate: String,
})

const emit = defineEmits(["change", "update:modelValue"])
const dayjs = inject("$dayjs")
const SUPPORTED_FIELD_TYPES = [
	"Link",
	"Select",
	"Small Text",
	"Text",
	"Long Text",
	"Check",
	"Data",
	"Float",
	"Int",
	"Section Break",
	"Date",
	"Time",
	"Datetime",
]

let linkFieldList = ref([])
let date = ref(null)

const showField = computed(() => {
	if (props.readOnly && !props.modelValue)
		return false

	return (
		SUPPORTED_FIELD_TYPES.includes(props.fieldtype)
		&& !props.hidden
	)
})

const selectionList = computed(() => {
	if (props.fieldtype == "Link" && props.options) {
		return props.documentList || linkFieldList.value.data
	} else if (props.fieldtype == "Select" && props.options) {
		const options = props.options.split("\n")
		return options.map((option) => ({
			label: option,
			value: option,
		}))
	}

	return []
})

function setLinkFieldList() {
	// get link field document list
	if (props.fieldtype == "Link" && props.options) {
		linkFieldList.value = createResource({
			url: "hrms.api.get_link_field_options",
			params: {
				doctype: props.options,
			},
			pageLength: 100,
			transform: (data) => {
				return data.map((doc) => ({
					label: doc.label ? `${doc.label}: ${doc.value}` : doc.value,
					value: doc.value,
				}))
			},
		})

		linkFieldList.value.reload()
	}
}

function setDefaultValue() {
	// set default values
	if (props.default) {
		props.fieldtype === "Check"
			? emit("update:modelValue", props.default === "1" ? true : false)
			: emit("update:modelValue", props.default)
	} else {
		props.fieldtype === "Check"
			? emit("update:modelValue", false)
			: emit("update:modelValue", "")
	}
}

onMounted(() => {
	setLinkFieldList()
	setDefaultValue()
})
</script>
