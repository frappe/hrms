<template>
	<Badge
		v-if="props.fieldtype === 'Select'"
		:colorMap="colorMap"
		:label="props.value"
	/>

	<div v-else-if="props.fieldtype === 'Date'" class="text-gray-900 text-base">
		{{ dayjs(props.value).format("D MMM") }}
	</div>

	<Input
		v-else-if="props.fieldtype === 'Check'"
		type="checkbox"
		label=""
		v-model="props.value"
		:disabled="true"
	/>

	<div
		v-else-if="['Small Text', 'Text', 'Long Text'].includes(props.fieldtype)"
		class="text-gray-900 text-base bg-gray-200 rounded-lg py-2.5 pl-3 mt-1"
	>
		{{ props.value }}
	</div>

	<EmployeeAvatar
		v-else-if="props.fieldtype === 'Link' && props.fieldname === 'employee'"
		:employeeID="props.value" :showLabel="true"
	/>

	<div v-else class="text-gray-900 text-base">{{ props.value }}</div>
</template>

<script setup>

import { Badge, Input } from "frappe-ui"

import dayjs from "@/utils/dayjs"
import EmployeeAvatar from "@/components/EmployeeAvatar.vue"

const props = defineProps({
	value: [String, Number, Boolean, Array, Object],
	fieldtype: String,
	fieldname: String,
})

const colorMap = {
	Approved: "green",
	Rejected: "red",
	Open: "yellow"
}

</script>