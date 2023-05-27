<template>
	<Avatar
		v-if="employeeID"
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
})

const employee = computed(() => getEmployeeInfo(props.employeeID))

</script>