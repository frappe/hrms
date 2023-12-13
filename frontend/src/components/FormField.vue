<template>
	<div v-if="showField" class="flex flex-col gap-1.5">
		<!-- Label -->
		<span
			v-if="
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

		<!-- Link & Select -->
		<Autocomplete
			v-if="['Link', 'Select'].includes(props.fieldtype)"
			ref="autocompleteRef"
			:class="isReadOnly ? 'pointer-events-none' : ''"
			:value="modelValue"
			:placeholder="`Select ${props.options}`"
			:options="selectionList"
			@change="(v) => emit('update:modelValue', v?.value)"
			@update:query="(q) => updateLinkFieldOptions(q)"
			v-bind="$attrs"
			:disabled="isReadOnly"
		/>

		<!-- Text -->
		<Input
			v-else-if="
				['Text Editor', 'Small Text', 'Text', 'Long Text'].includes(
					props.fieldtype
				)
			"
			type="textarea"
			:value="modelValue"
			:placeholder="`Enter ${props.label}`"
			@input="(v) => emit('update:modelValue', v)"
			@change="(v) => emit('change', v)"
			v-bind="$attrs"
			:disabled="isReadOnly"
			class="h-15"
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
			:disabled="isReadOnly"
			class="rounded-sm text-gray-800"
		/>

		<!-- Data field -->
		<Input
			v-else-if="props.fieldtype === 'Data'"
			type="text"
			:value="modelValue"
			@input="(v) => emit('update:modelValue', v)"
			@change="(v) => emit('change', v)"
			v-bind="$attrs"
			:disabled="isReadOnly"
		/>

		<!-- Read only currency field -->
		<Input
			v-else-if="props.fieldtype === 'Currency' && isReadOnly"
			type="text"
			:value="modelValue"
			@input="(v) => emit('update:modelValue', v)"
			@change="(v) => emit('change', v)"
			v-bind="$attrs"
			:disabled="isReadOnly"
		/>

		<!-- Float/Int field -->
		<Input
			v-else-if="isNumberType"
			type="number"
			:value="modelValue"
			@input="(v) => emit('update:modelValue', v)"
			@change="(v) => emit('change', v)"
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
				class="text-base font-semibold text-gray-800"
				:class="props.addSectionPadding ? 'pt-4' : ''"
			>
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
			:disabled="isReadOnly"
			:min="props.minDate"
			:max="props.maxDate"
		/>

		<!-- Time -->
		<!-- Datetime -->

		<ErrorMessage :message="props.errorMessage" />
	</div>
</template>

<script setup>
import { createResource, Autocomplete, ErrorMessage, debounce } from "frappe-ui"
import { ref, computed, onMounted, inject, watchEffect } from "vue"

const props = defineProps({
	fieldtype: String,
	fieldname: String,
	modelValue: [String, Number, Boolean, Array, Object],
	default: [String, Number, Boolean, Array, Object],
	label: String,
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

const emit = defineEmits(["change", "update:modelValue"])
const dayjs = inject("$dayjs")

let date = ref(null)
const autocompleteRef = ref(null)
const searchText = ref("")

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

const selectionList = computed(() => {
	if (props.fieldtype == "Link" && props.options) {
		return props.documentList || linkFieldList?.data
	} else if (props.fieldtype == "Select" && props.options) {
		const options = props.options.split("\n")
		return options.map((option) => ({
			label: option,
			value: option,
		}))
	}

	return []
})

const linkFieldList = createResource({
	url: "frappe.desk.search.search_link",
	params: {
		doctype: props.options,
		txt: searchText.value,
		filters: props.linkFilters,
	},
	transform: (data) => {
		return data.map((doc) => {
			const title = doc?.description?.split(",")?.[0]
			return {
				label: title ? `${title} : ${doc.value}` : doc.value,
				value: doc.value,
			}
		})
	},
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
		props.fieldtype === "Check"
			? emit("update:modelValue", false)
			: emit("update:modelValue", "")
	}
}

const updateLinkFieldOptions = debounce((query) => {
	searchText.value = query || ""
	linkFieldList.reload()
}, 500)

// get link field options from DB only when the field is clicked
watchEffect(() => {
	if (autocompleteRef.value && props.fieldtype === "Link") {
		autocompleteRef.value?.$refs?.search?.$el?.addEventListener("focus", () => {
			linkFieldList.reload()
		})
	}
})

onMounted(() => {
	setDefaultValue()
})
</script>
