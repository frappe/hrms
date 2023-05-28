<template>
	<div class="flex flex-col bg-white rounded-lg mt-5 overflow-auto" v-if="items">
		<div
			class="flex flex-row p-3.5 items-center justify-between border-b cursor-pointer"
			v-for="link in props.items" :key="link.name"
		>
			<LeaveRequestItem
				v-if="link.doctype === 'Leave Application'"
				:leave="link"
				:isTeamRequest="props.teamRequests"
			/>
		</div>
	</div>
	<div class="text-sm text-gray-500 mt-5 flex flex-col items-center" v-else>You have no requests</div>
</template>

<script setup>

import { ref } from "vue"

import LeaveRequestItem from "@/components/LeaveRequestItem.vue"

const props = defineProps({
	items: {
		type: Array,
	},
	teamRequests: {
		type: Boolean,
		default: false,
	}
})

</script>
