<template>
	<div class="w-full">
		<TabButtons
			:buttons="[{ label: 'My Requests'}, { label: 'Team Requests' }]"
			v-model="activeTab"
		/>
		<RequestList :items="myRequests.data" v-if="activeTab == 'My Requests'" />
		<RequestList :items="teamRequests.data" :teamRequests="true" v-if="activeTab == 'Team Requests'" />
	</div>
</template>

<script setup>

import { inject, ref } from "vue"
import { createResource, createListResource, toast } from "frappe-ui"
import dayjs from "@/utils/dayjs"

import TabButtons from "@/components/TabButtons.vue"
import RequestList from "@/components/RequestList.vue"

const employee = inject("$employee")
const activeTab = ref("My Requests")

const myRequests = createResource({
	url: "hrms.api.get_employee_leave_applications",
	params: {
		employee: employee.data.name,
	},
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
	auto: true,
	transform(data) {
		return transformLeaveData(data)
	}
})

const transformLeaveData = (data) => {
	return data.map((leave) => {
		leave.leave_dates = get_leave_dates(leave)
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