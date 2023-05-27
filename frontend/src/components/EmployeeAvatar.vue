<template>
	<Avatar
		v-if="empID"
		:label="employee?.employee_name"
		:imageURL="employee?.image"
		:size="props.size"
	/>
</template>

<script setup>

import { computed } from "vue"
import { Avatar } from "frappe-ui"
import { employeeInfo } from "@/data/employees"

const props = defineProps({
	empID: {
		type: String,
	},
	size: {
		type: String,
		default: "sm",
	},
})

const employee = computed(() => employeeInfo(props.empID))

</script>