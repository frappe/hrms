<template>
	<div class="w-full">
		<TabButtons
			:buttons="[{ label: 'My Requests' }, { label: 'Team Requests' }]"
			v-model="activeTab"
		/>
		<RequestList v-if="activeTab == 'My Requests'" :items="myRequests" />
		<RequestList
			v-else-if="activeTab == 'Team Requests'"
			:items="teamRequests"
			:teamRequests="true"
		/>
	</div>
</template>

<script setup>
import { ref, inject, onMounted, computed, markRaw } from "vue"

import TabButtons from "@/components/TabButtons.vue"
import RequestList from "@/components/RequestList.vue"

import { myAttendanceRequests, myShiftRequests } from "@/data/attendance"
import { myClaims, teamClaims } from "@/data/claims"
import { myLeaves, teamLeaves } from "@/data/leaves"

import AttendanceRequestItem from "@/components/AttendanceRequestItem.vue"
import ExpenseClaimItem from "@/components/ExpenseClaimItem.vue"
import LeaveRequestItem from "@/components/LeaveRequestItem.vue"
import ShiftRequestItem from "@/components/ShiftRequestItem.vue"

import { useListUpdate } from "@/composables/realtime"

const activeTab = ref("My Requests")
const socket = inject("$socket")

const myRequests = computed(() =>
	updateRequestDetails(myLeaves, myClaims, myAttendanceRequests, myShiftRequests)
)

const teamRequests = computed(() => updateRequestDetails(teamLeaves, teamClaims))

function updateRequestDetails(leaves, claims, attendanceRequests, shiftRequests) {
	const requests = [leaves, claims, attendanceRequests, shiftRequests].reduce(
		(acc, resource) => acc.concat(resource.data || []),
		[]
	)

	const componentMap = {
		"Leave Application": LeaveRequestItem,
		"Expense Claim": ExpenseClaimItem,
		"Attendance Request": AttendanceRequestItem,
		"Shift Request": ShiftRequestItem,
	}
	requests.forEach((request) => {
		request.component = markRaw(componentMap[request.doctype])
	})

	return getSortedRequests(requests)
}

function getSortedRequests(list) {
	// return top 10 requests sorted by posting date
	return list
		.sort((a, b) => {
			return new Date(b.creation) - new Date(a.creation)
		})
		.splice(0, 10)
}

onMounted(() => {
	useListUpdate(socket, "Leave Application", () => teamLeaves.reload())
	useListUpdate(socket, "Expense Claim", () => teamClaims.reload())
})
</script>
