<template>
	<div
		class="flex flex-col bg-white rounded-lg mt-5 overflow-auto"
		v-if="props.items?.length"
	>
		<div
			class="flex flex-row p-3.5 items-center justify-between border-b cursor-pointer"
			v-for="link in props.items"
			:key="link.name"
			@click="openRequestModal(link)"
		>
			<LeaveRequestItem
				v-if="link.doctype === 'Leave Application'"
				:leave="link"
				:isTeamRequest="props.teamRequests"
			/>
		</div>
	</div>
	<EmptyState message="You have no requests" v-else />

	<ion-modal
		ref="modal"
		:is-open="isRequestModalOpen"
		@didDismiss="closeRequestModal"
		:initial-breakpoint="1"
		:breakpoints="[0, 1]"
	>
		<RequestActionSheet :fields="LEAVE_FIELDS" :data="selectedRequest" />
	</ion-modal>
</template>

<script setup>
import { ref } from "vue"
import { IonModal } from "@ionic/vue"

import LeaveRequestItem from "@/components/LeaveRequestItem.vue"
import RequestActionSheet from "@/components/RequestActionSheet.vue"

import { LEAVE_FIELDS } from "@/data/config/requestSummaryFields"

const props = defineProps({
	items: {
		type: Array,
	},
	teamRequests: {
		type: Boolean,
		default: false,
	},
})

const isRequestModalOpen = ref(false)
const selectedRequest = ref(null)

const openRequestModal = async (request) => {
	selectedRequest.value = request
	isRequestModalOpen.value = true
}

const closeRequestModal = async (request) => {
	isRequestModalOpen.value = false
	selectedRequest.value = null
}
</script>
