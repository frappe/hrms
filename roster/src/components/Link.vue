<template>
	<div>
		<span class="block text-xs leading-5 text-gray-600">
			{{ props.label }}
		</span>
		<Autocomplete
			ref="autocompleteRef"
			size="sm"
			v-model="value"
			:options="options.data || []"
			:class="disabled ? 'pointer-events-none' : ''"
			:disabled="disabled"
			@update:query="handleQueryUpdate"
		/>
	</div>
</template>

<script setup>
import { createResource, Autocomplete, debounce } from "frappe-ui";
import { ref, computed, watch } from "vue";

const props = defineProps({
	doctype: {
		type: String,
		required: true,
	},
	modelValue: {
		type: String,
		required: false,
		default: "",
	},
	filters: {
		type: Object,
		default: {},
	},
	disabled: {
		type: Boolean,
		default: false,
	},
	label: {
		type: String,
		default: "",
	},
});

const emit = defineEmits(["update:modelValue"]);

const autocompleteRef = ref(null);
const searchText = ref("");

const value = computed({
	get: () => props.modelValue,
	set: (val) => {
		const newVal = val && typeof val === "object" && val.value !== undefined ? val.value : val;
		console.log(newVal);
		emit("update:modelValue", newVal || "");
	},
});

const options = createResource({
	url: "frappe.desk.search.search_link",
	params: {
		doctype: props.doctype,
		txt: searchText.value,
		filters: props.filters,
	},
	method: "POST",
	transform: (data) => {
		return data.map((doc) => {
			const title = doc?.description?.split(",")?.[0];
			return {
				label: title ? `${title} : ${doc.value}` : doc.value,
				value: doc.value,
			};
		});
	},
});

const reloadOptions = (searchTextVal) => {
	options.update({
		params: {
			txt: searchTextVal,
			doctype: props.doctype,
		},
	});
	options.reload();
};

const handleQueryUpdate = debounce((newQuery) => {
	const val = newQuery || "";

	if (val === "" && props.modelValue) return;

	if (searchText.value === val) return;
	searchText.value = val;
	reloadOptions(val);
}, 300);

watch(
	() => props.doctype,
	() => {
		if (!props.doctype || props.doctype === options.doctype) return;
		reloadOptions("");
	},
	{ immediate: true },
);
</script>
