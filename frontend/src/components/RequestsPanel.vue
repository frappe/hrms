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
import { createResource, createListResource, toast } from "frappe-ui"
import RequestsList from "@/components/RequestsList.vue"
import dayjs from "@/utils/dayjs"

const employee = inject("$employee")
const activeTab = ref("My Requests")

const myRequests = createResource({
	url: "hrms.api.get_employee_leave_applications",
	params: {
		employee: employee.data.name,
	},
	cache: "MyLeaveRequests",
	auto: true,
	transform(data) {
		return transformLeaveData(data)
	}
})

const teamRequests = createResource({
	url: "hrms.api.get_team_leave_applications",
	params: {
		employee: employee.data.name,
		user_id: employee.data.user_id,
	},
	cache: "TeamLeaveRequests",
	auto: true,
	transform(data) {
		return transformLeaveData(data)
	}
})

const transformLeaveData = (data) => {
	return data.map((leave) => {
		leave.leave_dates = get_leave_dates(leave)
		leave.total_leave_days = `${leave.total_leave_days}d`
		leave.doctype = "Leave Application"
		return leave
	})
}

const get_leave_dates = (leave) => {
	if (leave.from_date == leave.to_date)
		return dayjs(leave.from_date).format("D MMM")
	else
		return `${dayjs(leave.from_date).format("D MMM")} - ${dayjs(leave.to_date).format("D MMM")}`
}

</script>