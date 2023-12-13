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
import { ref, inject, onMounted, computed, markRaw, onBeforeUnmount } from "vue"

import TabButtons from "@/components/TabButtons.vue"
import RequestList from "@/components/RequestList.vue"

import { myLeaves, teamLeaves } from "@/data/leaves"
import { myClaims, teamClaims } from "@/data/claims"

import LeaveRequestItem from "@/components/LeaveRequestItem.vue"
import ExpenseClaimItem from "@/components/ExpenseClaimItem.vue"

const activeTab = ref("My Requests")

const socket = inject("$socket")
const employee = inject("$employee")

const myRequests = computed(() => {
	const requests = [...(myLeaves.data || []), ...(myClaims.data || [])]

	return requests.map((item) => {
		if (item.doctype === "Leave Application")
			item.component = markRaw(LeaveRequestItem)
		else if (item.doctype === "Expense Claim")
			item.component = markRaw(ExpenseClaimItem)

		return item
	})
})

const teamRequests = computed(() => {
	const requests = [...(teamLeaves.data || []), ...(teamClaims.data || [])]

	return requests.map((item) => {
		if (item.doctype === "Leave Application")
			item.component = markRaw(LeaveRequestItem)
		else if (item.doctype === "Expense Claim")
			item.component = markRaw(ExpenseClaimItem)

		return item
	})
})

onMounted(() => {
	socket.emit("doctype_subscribe", "Leave Application")
	socket.emit("doctype_subscribe", "Expense Claim")
	socket.on("list_update", (data) => {
		if (data.doctype === "Leave Application") {
			myLeaves.reload()
			teamLeaves.reload()
		} else if (data.doctype === "Expense Claim") {
			myClaims.reload()
			teamClaims.reload()
		}
	})
})

onBeforeUnmount(() => {
	socket.emit("doctype_unsubscribe", "Leave Application")
	socket.emit("doctype_unsubscribe", "Expense Claim")
	socket.off("list_update")
})
</script>
