<template>
	<div
		class="flex flex-col bg-white rounded mt-5 overflow-auto"
		v-if="props.items?.length"
	>
		<div
			class="flex flex-row p-3.5 items-center justify-between border-b cursor-pointer"
			v-for="link in props.items"
			:key="link.name"
			@click="openRequestModal(link)"
		>
			<component
				:is="props.component || link.component"
				:doc="link"
				:workflowStateField="link.workflow_state_field"
				:isTeamRequest="props.teamRequests"
			/>
		</div>

		<router-link
			v-if="props.addListButton"
			:to="{ name: props.listButtonRoute }"
			v-slot="{ navigate }"
		>
			<Button
				variant="ghost"
				@click="navigate"
				class="w-full !text-gray-600 py-6 text-sm border-none bg-white hover:bg-white"
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
		<RequestActionSheet
			:fields="
				selectedRequest.doctype === 'Leave Application'
					? LEAVE_FIELDS
					: EXPENSE_CLAIM_FIELDS
			"
			v-model="selectedRequest"
		/>
	</ion-modal>
</template>

<script setup>
import { ref } from "vue"
import { IonModal } from "@ionic/vue"
import RequestActionSheet from "@/components/RequestActionSheet.vue"

import {
	LEAVE_FIELDS,
	EXPENSE_CLAIM_FIELDS,
} from "@/data/config/requestSummaryFields"

const props = defineProps({
	component: {
		type: Object,
	},
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

const closeRequestModal = async () => {
	isRequestModalOpen.value = false
	selectedRequest.value = null
}
</script>
