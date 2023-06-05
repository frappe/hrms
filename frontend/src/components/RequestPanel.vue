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

import { ref } from "vue"

import TabButtons from "@/components/TabButtons.vue"
import RequestList from "@/components/RequestList.vue"

import { myRequests, teamRequests } from "@/data/leaves"

const activeTab = ref("My Requests")

</script>