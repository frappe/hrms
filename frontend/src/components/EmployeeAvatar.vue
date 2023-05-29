<template>
	<div v-if="showLabel" class="flex flex-row items-center gap-2">
		<Avatar
			v-if="employeeID"
			:label="employee?.employee_name"
			:imageURL="employee?.image"
			:size="props.size"
		/>
		<div class="text-base text-gray-800 grow">{{ employee?.employee_name }}</div>
	</div>

	<Avatar
		v-else
		:label="employee?.employee_name"
		:imageURL="employee?.image"
		:size="props.size"
	/>
</template>

<script setup>

import { computed } from "vue"
import { Avatar } from "frappe-ui"
import { getEmployeeInfo } from "@/data/employees"

const props = defineProps({
	employeeID: {
		type: String,
	},
	size: {
		type: String,
		default: "sm",
	},
	showLabel: {
		type: Boolean,
		default: false,
	}
})

const employee = computed(() => getEmployeeInfo(props.employeeID))

</script>