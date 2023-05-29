<template>
	<Badge
		v-if="props.fieldtype === 'Select'"
		:colorMap="colorMap"
		:label="props.value"
	/>

	<div v-else-if="props.fieldtype === 'Date'" class="text-gray-900 text-base">
		{{ dayjs(props.value).format("D MMM") }}
	</div>

	<EmployeeAvatar
		v-else-if="props.fieldtype === 'Link' && props.fieldname === 'employee'"
		:employeeID="props.value" showLabel="true"
	/>

	<div v-else class="text-gray-900 text-base">{{ props.value }}</div>
</template>

<script setup>

import { Badge } from "frappe-ui"
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