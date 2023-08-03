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
				:doc="link"
				:isTeamRequest="props.teamRequests"
			/>
			<ExpenseClaimItem
				v-else-if="link.doctype === 'Expense Claim'"
				:doc="link"
				:isTeamRequest="props.teamRequests"
			/>
			<EmployeeAdvanceItem
				v-else-if="link.doctype === 'Employee Advance'"
				:doc="link"
			/>
		</div>

		<router-link
			v-if="props.addListButton"
			:to="{ name: props.listButtonRoute }"
			v-slot="{ navigate }"
		>
			<Button
				@click="navigate"
				class="w-full !text-gray-600 py-4 mt-0 border-none bg-white hover:bg-white"
			>
				View List
			</Button>
		</router-link>
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
import ExpenseClaimItem from "@/components/ExpenseClaimItem.vue"
import RequestActionSheet from "@/components/RequestActionSheet.vue"
import EmployeeAdvanceItem from "@/components/EmployeeAdvanceItem.vue"

import { LEAVE_FIELDS } from "@/data/config/requestSummaryFields"

const props = defineProps({
	items: {
		type: Array,
	},
	teamRequests: {
		type: Boolean,
		default: false,
	},
	addListButton: {
		type: Boolean,
		default: false,
	},
	listButtonRoute: {
		type: String,
		default: "",
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
