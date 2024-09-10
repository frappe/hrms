<template>
	<BaseLayout pageTitle="Attendance">
		<template #body>
			<div class="flex flex-col mt-7 mb-7 p-4 gap-7">
				<AttendanceCalendar />
				<div class="w-full">
					<router-link :to="{ name: 'AttendanceRequestFormView' }" v-slot="{ navigate }">
						<Button @click="navigate" variant="solid" class="w-full py-5 text-base">
							Request Attendance
						</Button>
					</router-link>
				</div>
				<div>
					<div class="text-lg text-gray-800 font-bold">Recent Attendance Requests</div>
					<RequestList
						:component="markRaw(AttendanceRequestItem)"
						:items="attendanceRequests?.data?.slice(0, 5)"
						:addListButton="true"
						listButtonRoute="AttendanceRequestListView"
					/>
				</div>
				<div>
					<div class="text-lg text-gray-800 font-bold">Recent Shift Requests</div>
					<RequestList
						:component="markRaw(ShiftRequestItem)"
						:items="shiftRequests?.data?.slice(0, 5)"
						:addListButton="true"
						listButtonRoute="ShiftRequestListView"
					/>
				</div>
				<div>
					<div class="text-lg text-gray-800 font-bold">Upcoming Shifts</div>
					<RequestList
						:component="markRaw(ShiftAssignmentItem)"
						:items="upcomingShifts"
						:addListButton="true"
						listButtonRoute="ShiftAssignmentListView"
						emptyStateMessage="You have no upcoming shifts"
					/>
				</div>
			</div>
		</template>
	</BaseLayout>
</template>

<script setup>
import { computed, inject, markRaw } from "vue"
import { createListResource, createResource } from "frappe-ui"

import BaseLayout from "@/components/BaseLayout.vue"
import AttendanceRequestItem from "@/components/AttendanceRequestItem.vue"
import ShiftRequestItem from "@/components/ShiftRequestItem.vue"
import ShiftAssignmentItem from "@/components/ShiftAssignmentItem.vue"
import RequestList from "@/components/RequestList.vue"
import AttendanceCalendar from "@/components/AttendanceCalendar.vue"

import { getDates, getTotalDays, getShiftDates, getTotalShiftDays, getShiftTiming } from "@/data/attendance"

const employee = inject("$employee")
const dayjs = inject("$dayjs")

const attendanceRequests = createListResource({
	doctype: "Attendance Request",
	fields: ["name", "reason", "from_date", "to_date", "include_holidays", "shift", "docstatus"],
	filters: {
		employee: employee.data?.name,
		docstatus: ["!=", 2],
	},
	orderBy: "modified desc",
	auto: true,
	cache: "hrms:attendance_requests",
	transform: (data) => {
		return data.map((request) => {
			request.doctype = "Attendance Request"
			request.attendance_dates = getDates(request)
			request.total_attendance_days = getTotalDays(request)
			return request
		})
	},
})

const shiftRequests = createListResource({
	doctype: "Shift Request",
	fields: ["name", "shift_type", "from_date", "to_date", "status", "docstatus"],
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
			request.shift_dates = getDates(request)
			request.total_shift_days = getTotalDays(request)
			return request
		})
	},
})

const shifts = createResource({
	url: "hrms.api.get_shifts",
	auto: true,
	cache: "hrms:shifts",
	makeParams() {
		return {
			employee: employee.data?.name,
		}
	},
	transform: (data) => {
		return data.map((assignment) => {
			assignment.doctype = "Shift Assignment"
			assignment.is_upcoming = !assignment.end_date || dayjs(assignment.end_date).isAfter(dayjs())
			assignment.shift_dates = getShiftDates(assignment)
			assignment.total_shift_days = getTotalShiftDays(assignment)
			assignment.shift_timing = getShiftTiming(assignment)
			return assignment
		})
	},
})

const upcomingShifts = computed(() => {
	const filteredShifts = shifts.data?.filter((shift) => shift.is_upcoming)

	// show only 5 upcoming shifts
	return filteredShifts?.slice(0, 5)
})
</script>
