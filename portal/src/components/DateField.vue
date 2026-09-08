<template>
	<!--
		FormControl has no `date` branch, so type="date" falls through to a native
		browser input. DatePicker is the design-system control. Its `label` prop is
		forwarded to TextInput, which does not render labels in 0.1.278, so the
		label markup here mirrors FormControl's.
	-->
	<div class="flex flex-col gap-1.5">
		<label v-if="label" class="block text-base text-ink-gray-5">
			{{ label }}
			<span v-if="required" class="text-ink-red-3">*</span>
		</label>
		<DatePicker
			class="w-full"
			input-class="w-full"
			:model-value="modelValue"
			:placeholder="placeholder"
			format="D MMM YYYY"
			@update:model-value="$emit('update:modelValue', $event)"
		/>
	</div>
</template>

<script setup>
import { DatePicker } from "frappe-ui";

defineProps({
	modelValue: String,
	label: String,
	required: Boolean,
	placeholder: { type: String, default: "Select a date" },
});
defineEmits(["update:modelValue"]);
</script>
