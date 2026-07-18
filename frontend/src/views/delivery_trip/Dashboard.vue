<template>
	<BaseLayout>
		<template #body>
			<div class="flex flex-col items-center my-7 p-4 gap-7 bg-[var(--color-bg-page)]">
				<DeliveryTripSummary />

				<TodayTrips @openTrip="openTrip" />

				<router-link
					:to="{ name: 'DeliveryTripListPage' }"
					v-slot="{ navigate }"
					class="w-full"
				>
					<Button
						variant="ghost"
						@click="navigate"
						class="w-full !text-[var(--color-primary)] py-6 text-sm border-none bg-transparent hover:bg-transparent"
					>
						{{ __("View List") }}
					</Button>
				</router-link>
			</div>

			<ion-modal
				ref="modal"
				:is-open="isModalOpen"
				@didDismiss="closeTrip"
				:initial-breakpoint="1"
				:breakpoints="[0, 1]"
			>
				<DeliveryTripActionSheet v-model="selectedTrip" @tripUpdated="closeTrip" />
			</ion-modal>
		</template>
	</BaseLayout>
</template>

<script setup>
import { ref, inject } from "vue"
import { IonModal } from "@ionic/vue"

import BaseLayout from "@/components/BaseLayout.vue"
import DeliveryTripSummary from "@/components/DeliveryTripSummary.vue"
import TodayTrips from "@/components/TodayTrips.vue"
import DeliveryTripActionSheet from "@/components/DeliveryTripActionSheet.vue"

const __ = inject("$translate")

const isModalOpen = ref(false)
const selectedTrip = ref(null)

function openTrip(trip) {
	selectedTrip.value = trip
	isModalOpen.value = true
}

function closeTrip() {
	isModalOpen.value = false
	selectedTrip.value = null
}
</script>