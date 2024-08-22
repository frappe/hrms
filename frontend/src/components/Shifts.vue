<template>
	<div class="flex flex-col gap-5 w-full">
		<div class="flex flex-row justify-between items-center">
			<div class="text-lg text-gray-800 font-bold">Upcoming Shifts</div>
			<div
				v-if="shifts?.data?.length"
				class="text-sm text-gray-800 font-semibold cursor-pointer underline underline-offset-2"
			>
				View All
			</div>
		</div>

		<div v-if="upcomingShifts?.length" class="flex flex-col bg-white rounded">
			<div
				class="p-3.5 items-center justify-between border-b cursor-pointer"
				v-for="shift in upcomingShifts"
				:key="shift.name"
				@click="openRequestModal(shift)"
			>
				<div class="flex flex-col w-full justify-center gap-2.5">
					<div class="flex flex-row items-center justify-between">
						<div class="flex flex-row items-start gap-3 grow">
							<FeatherIcon name="clock" class="h-5 w-5 text-gray-500" />
							<div class="flex flex-col items-start gap-1.5">
								<div class="text-base font-normal text-gray-800">
									{{ shift.shift_type }}
								</div>
								<div class="text-xs font-normal text-gray-500">
									<span>{{ shift.shift_dates }}</span>
									<span v-if="shift.end_date" class="whitespace-pre"> &middot; </span>
									<span v-if="shift.end_date" class="whitespace-nowrap">{{
										`${shift.total_shift_days}d`
									}}</span>
								</div>
							</div>
						</div>
						<div class="flex flex-row justify-end items-center gap-2">
							<span class="text-gray-700 font-normal rounded text-base">
								{{ shift.shift_timing }}
							</span>
							<FeatherIcon name="chevron-right" class="h-5 w-5 text-gray-500" />
						</div>
					</div>
				</div>
			</div>
		</div>

		<EmptyState v-else message="You have no upcoming shifts" />
	</div>

	<ion-modal
		ref="modal"
		:is-open="isRequestModalOpen"
		@didDismiss="closeRequestModal"
		:initial-breakpoint="1"
		:breakpoints="[0, 1]"
	>
		<RequestActionSheet :fields="SHIFT_FIELDS" v-model="selectedRequest" />
	</ion-modal>
</template>

<script setup>
import { computed, ref } from "vue"
import { IonModal } from "@ionic/vue"
import { FeatherIcon } from "frappe-ui"

import RequestActionSheet from "@/components/RequestActionSheet.vue"
import EmptyState from "@/components/EmptyState.vue"
import { shifts } from "@/data/attendance"
import { SHIFT_FIELDS } from "@/data/config/requestSummaryFields"

const isRequestModalOpen = ref(false)
const selectedRequest = ref(null)

const upcomingShifts = computed(() => {
	const filteredShifts = shifts.data?.filter((shift) => shift.is_upcoming)

	// show only 5 upcoming shifts
	return filteredShifts?.slice(0, 5)
})

const openRequestModal = async (request) => {
	selectedRequest.value = request
	selectedRequest.value.doctype = "Shift Assignment"
	isRequestModalOpen.value = true
}

const closeRequestModal = async () => {
	isRequestModalOpen.value = false
	selectedRequest.value = null
}
</script>
