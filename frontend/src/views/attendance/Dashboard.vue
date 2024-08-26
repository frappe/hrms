<template>
	<BaseLayout pageTitle="Attendance">
		<template #body>
			<div class="flex flex-col mt-7 mb-7 p-4 gap-7">
				<AttendanceCalendar />

				<div>
					<div class="text-lg text-gray-800 font-bold">Recent Shift Requests</div>
					<RequestList
						:component="markRaw(ShiftRequestItem)"
						:items="shiftRequests?.data?.slice(0, 5)"
						:addListButton="true"
						listButtonRoute="ShiftRequestListView"
					/>
				</div>

				<Shifts />
			</div>
		</template>
	</BaseLayout>
</template>

<script setup>
import { inject, markRaw } from "vue"
import { createListResource } from "frappe-ui"

import BaseLayout from "@/components/BaseLayout.vue"
import ShiftRequestItem from "@/components/ShiftRequestItem.vue"
import RequestList from "@/components/RequestList.vue"
import AttendanceCalendar from "@/components/AttendanceCalendar.vue"
import Shifts from "@/components/Shifts.vue"

import { getShiftRequestDates, getTotalShiftRequestDays } from "@/data/attendance"

const employee = inject("$employee")

const shiftRequests = createListResource({
	doctype: "Shift Request",
	fields: ["name", "shift_type", "from_date", "to_date", "approver", "status", "docstatus"],
	filters: {
		employee: employee.data?.name,
		docstatus: ["!=", 2],
	},
	orderBy: "modified desc",
	auto: true,
	cache: "hrms:shift_requests",
	transform: (data) => {
		return data.map((request) => {
			request.doctype = "Shift Request"
			request.shift_dates = getShiftRequestDates(request)
			request.total_shift_days = getTotalShiftRequestDays(request)
			return request
		})
	},
})
</script>
