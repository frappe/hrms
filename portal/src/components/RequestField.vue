<template>
	<DateField
		v-if="field.type === 'date'"
		:model-value="modelValue"
		:label="field.label"
		:required="field.required"
		@update:model-value="$emit('update:modelValue', $event)"
	/>
	<FormControl
		v-else
		:model-value="modelValue"
		:type="controlType"
		:label="field.label"
		:options="options"
		:placeholder="field.placeholder"
		:required="field.type === 'checkbox' ? undefined : field.required"
		@update:model-value="$emit('update:modelValue', $event)"
	/>
</template>

<script setup>
import { computed } from "vue";
import { FormControl } from "frappe-ui";

import DateField from "@/components/DateField.vue";

const props = defineProps({
	field: { type: Object, required: true },
	modelValue: { type: [String, Number, Boolean], default: "" },
});
defineEmits(["update:modelValue"]);

const controlType = computed(
	() =>
		({ number: "number", textarea: "textarea", select: "select", checkbox: "checkbox" })[
			props.field.type
		] || "text",
);

const options = computed(() => {
	if (props.field.type !== "select") return undefined;
	return [
		{ label: `Select a ${props.field.label.toLowerCase()}`, value: "" },
		...(props.field.options || []).map((o) => ({ label: o, value: o })),
	];
});
</script>
