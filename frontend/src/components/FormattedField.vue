<template>
	<div v-if="!props.value" class="text-gray-600 text-base">-</div>

	<Badge
		v-else-if="props.fieldtype === 'Select'"
		variant="outline"
		:theme="colorMap[props.value]"
		:label="props.value"
		size="md"
	/>

	<div v-else-if="props.fieldtype === 'Date'" class="text-gray-900 text-base">
		{{ dayjs(props.value).format("D MMM YYYY") }}
	</div>

	<Input
		v-else-if="props.fieldtype === 'Check'"
		type="checkbox"
		label=""
		v-model="props.value"
		:disabled="true"
		class="rounded-sm text-gray-800"
	/>

	<div
		v-else-if="['Small Text', 'Text', 'Long Text'].includes(props.fieldtype)"
		class="text-gray-900 text-base bg-gray-100 rounded py-3 pl-3 mt-2"
	>
		{{ props.value }}
	</div>

	<EmployeeAvatar
		v-else-if="
			props.fieldtype === 'Link' &&
			['employee', 'reports_to'].includes(props.fieldname)
		"
		:employeeID="props.value"
		:showLabel="true"
	/>

	<div v-else class="text-gray-900 text-base">{{ props.value }}</div>
</template>

<script setup>
import { inject } from "vue"
import { Badge, FormControl, Input } from "frappe-ui"

import EmployeeAvatar from "@/components/EmployeeAvatar.vue"

const dayjs = inject("$dayjs")

const props = defineProps({
	value: [String, Number, Boolean, Array, Object],
	fieldtype: String,
	fieldname: String,
})

const colorMap = {
	Approved: "green",
	Rejected: "red",
	Open: "orange",
}
</script>
