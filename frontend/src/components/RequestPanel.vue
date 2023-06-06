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

import { ref, inject, onUnmounted } from "vue"

import TabButtons from "@/components/TabButtons.vue"
import RequestList from "@/components/RequestList.vue"

import { myRequests, teamRequests } from "@/data/leaves"

const activeTab = ref("My Requests")

const socket = inject("$socket")
const employee = inject("$employee")
const user = inject("$user")

socket.on("hrms:update_leaves", (data) => {
	if (data.employee === employee.data.name) {
		myRequests.reload()
	}
	if (data.approver === user.data.name) {
		teamRequests.reload()
	}
})

onUnmounted(() => {
	socket.off("hrms:update_leaves");
});

</script>