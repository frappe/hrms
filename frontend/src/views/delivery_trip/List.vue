<template>
	<ion-page>
		<ion-header class="ion-no-border">
			<div class="w-full sm:w-96">
				<div
					class="flex flex-row bg-[var(--color-surface)] shadow-sm py-4 px-3 items-center justify-between border-b"
				>
					<div class="flex flex-row items-center">
						<Button variant="ghost" class="!px-1 mr-1 hover:bg-white" @click="router.back()">
							<FeatherIcon name="chevron-left" class="h-5 w-5" />
						</Button>
						<h2 class="text-xl font-semibold text-[var(--color-primary)]">
							{{ __("Delivery Trips") }}
						</h2>
					</div>

					<Button
						icon="filter"
						variant="subtle"
						:class="[
							statusFilter
								? '!border !border-[var(--color-primary)] !bg-[var(--color-card-bg)] !text-[var(--color-primary)] !font-semibold'
								: '',
						]"
						@click="showFilters = !showFilters"
					/>
				</div>

				<div v-if="showFilters" class="flex flex-row gap-2 p-3 border-b bg-[var(--color-surface)]">
					<select
						v-model="statusFilter"
						class="w-full rounded border border-[var(--color-card-border)] text-sm py-2 px-2 text-gray-700"
					>
						<option value="">{{ __("All Statuses") }}</option>
						<option v-for="status in activeGroupStatuses" :key="status" :value="status">
							{{ __(status) }}
						</option>
					</select>
				</div>
			</div>
		</ion-header>

		<ion-content>
			<div class="flex flex-col items-center mb-7 p-4 h-full w-full sm:w-96 overflow-y-auto">
				<div class="w-full">
					<TabButtons :buttons="TAB_BUTTONS" v-model="activeTab" />

					<div
						class="flex flex-col bg-[var(--color-surface)] rounded mt-5"
						v-if="!loading && filteredTrips.length"
					>
						<div
							class="p-3.5 items-center justify-between border-b cursor-pointer"
							v-for="trip in filteredTrips"
							:key="trip.name"
							@click="openTrip(trip)"
						>
							<DeliveryTripItem :doc="trip" />
						</div>
					</div>
					<EmptyState :message="__('No trips found')" v-else-if="!loading" />

					<div v-if="loading" class="flex mt-2 items-center justify-center">
						<LoadingIndicator class="w-8 h-8 text-[var(--color-primary)]" />
					</div>
				</div>
			</div>
		</ion-content>

		<ion-modal
			ref="modal"
			:is-open="isModalOpen"
			@didDismiss="closeTrip"
			:initial-breakpoint="1"
			:breakpoints="[0, 1]"
		>
			<DeliveryTripActionSheet v-model="selectedTrip" @tripUpdated="onTripUpdated" />
		</ion-modal>
	</ion-page>
</template>

<script setup>
import { ref, computed, watch, inject, onMounted } from "vue"
import { useRouter } from "vue-router"
import { IonPage, IonHeader, IonContent, IonModal } from "@ionic/vue"
import { FeatherIcon, LoadingIndicator } from "frappe-ui"

import TabButtons from "@/components/TabButtons.vue"
import DeliveryTripItem from "@/components/DeliveryTripItem.vue"
import DeliveryTripActionSheet from "@/components/DeliveryTripActionSheet.vue"

import { fetchTripsByStatusGroup, STATUS_GROUPS } from "@/data/deliveryTrips"

const __ = inject("$translate")
const router = useRouter()

const TAB_BUTTONS = ["Active", "History"] // __("Active"), __("History")
const activeTab = ref(TAB_BUTTONS[0])
const showFilters = ref(false)
const statusFilter = ref("")

const trips = ref([])
const loading = ref(true)

const isModalOpen = ref(false)
const selectedTrip = ref(null)

const activeGroupKey = computed(() => (activeTab.value === "Active" ? "active" : "history"))
const activeGroupStatuses = computed(() => STATUS_GROUPS[activeGroupKey.value])

const filteredTrips = computed(() => {
	if (!statusFilter.value) return trips.value
	return trips.value.filter((trip) => trip.status === statusFilter.value)
})

async function loadTrips() {
	loading.value = true
	try {
		trips.value = await fetchTripsByStatusGroup(activeGroupKey.value)
	} finally {
		loading.value = false
	}
}

function openTrip(trip) {
	selectedTrip.value = trip
	isModalOpen.value = true
}

function closeTrip() {
	isModalOpen.value = false
	selectedTrip.value = null
}

function onTripUpdated() {
	closeTrip()
	loadTrips()
}

watch(activeTab, () => {
	statusFilter.value = ""
	loadTrips()
})

onMounted(loadTrips)
</script>