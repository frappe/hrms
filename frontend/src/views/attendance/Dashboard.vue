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
						listButtonRoute="LeaveApplicationListView"
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
import { getLeaveDates } from "@/data/leaves"

const employee = inject("$employee")
const dayjs = inject("$dayjs")

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
			request.shift_dates = getLeaveDates(request)
			request.total_shift_days = getTotalShiftDays(request)
			return request
		})
	},
})

const getTotalShiftDays = (shift) => {
	if (!shift.to_date) return null
	const to_date = dayjs(shift.to_date)
	const from_date = dayjs(shift.from_date)
	return to_date.diff(from_date, "d") + 1
}
</script>
