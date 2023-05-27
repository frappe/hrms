<template>
	<div class="w-full">
		<TabButtons
			:buttons="[{ label: 'My Requests'}, { label: 'Team Requests' }]"
			v-model="activeTab"
		/>
		<RequestsList :items="myRequests.data" v-if="activeTab == 'My Requests'" />
		<RequestsList :items="teamRequests.data" :teamRequests="true" v-if="activeTab == 'Team Requests'" />
	</div>
</template>

<script setup>

import { inject, ref } from "vue"
import TabButtons from "@/components/TabButtons.vue"
import { createListResource, toast } from "frappe-ui"
import RequestsList from "@/components/RequestsList.vue"

const employee = inject("$employee")
const activeTab = ref("My Requests")

const myRequests = createListResource({
	doctype: "Leave Application",
	fields: ["name", "employee", "employee_name", "leave_type", "status", "from_date", "to_date"],
	filters: {
		employee: employee.data.name,
		status: ["!=", "Cancelled"],
	},
	orderBy: "from_date desc",
})
myRequests.reload()

const teamRequests = createListResource({
	doctype: "Leave Application",
	fields: ["name", "employee", "employee_name", "leave_type", "status", "from_date", "to_date"],
	filters: {
		leave_approver: employee.data.user_id,
		status: ["!=", "Cancelled"],
		employee: ["!=", employee.data.name],
	},
	orderBy: "from_date desc"
})
teamRequests.reload()

</script>