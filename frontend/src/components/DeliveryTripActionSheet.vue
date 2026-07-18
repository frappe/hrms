<template>
	<div
		v-if="trip"
		class="bg-[var(--color-surface)] w-full flex flex-col items-center justify-center pb-5 max-h-[calc(100vh-5rem)]"
	>
		<!-- Header -->
		<div
			class="w-full flex flex-row gap-2 pt-8 pb-5 border-b justify-center items-center sticky top-0 z-[100]"
		>
			<span class="text-[var(--color-primary)] font-bold text-lg text-center">
				{{ trip.name }}
			</span>
		</div>

		<!-- Trip Summary -->
		<div class="w-full p-4 overflow-auto">
			<div class="flex flex-col items-center justify-center gap-4">
				<div
					v-for="row in detailRows"
					:key="row.label"
					class="flex flex-row items-center justify-between w-full"
				>
					<div class="text-gray-600 text-base">{{ __(row.label) }}</div>
					<div class="text-gray-800 text-base font-medium text-right">{{ row.value }}</div>
				</div>

				<div class="flex flex-row items-center justify-between w-full">
					<div class="text-gray-600 text-base">{{ __("Status") }}</div>
					<span
						class="px-2 py-0.5 rounded-full text-xs font-medium bg-[var(--color-card-selected-bg)] text-[var(--color-primary)]"
					>
						{{ trip.status }}
					</span>
				</div>

				<div v-if="locationStatus" class="text-xs text-[var(--color-blue-muted)] text-center">
					{{ locationStatus }}
				</div>
			</div>
		</div>

		<!-- Actions -->
		<div
			v-if="trip.status === 'Scheduled'"
			class="flex w-full flex-row items-center justify-between gap-3 sticky bottom-0 border-t z-[100] p-4"
		>
			<Button
				@click="handleStartTrip"
				class="w-full py-5 !bg-[var(--color-primary)] hover:!bg-[var(--color-primary-hover)] !text-white"
				variant="solid"
				:loading="isProcessing"
			>
				<template #prefix>
					<FeatherIcon name="play" class="w-4" />
				</template>
				{{ __("Start Trip") }}
			</Button>
		</div>

		<div
			v-else-if="trip.status === 'In Transit'"
			class="flex w-full flex-row items-center justify-between gap-3 sticky bottom-0 border-t z-[100] p-4"
		>
			<Button
				@click="handleEndTrip"
				class="w-full py-5 !bg-[var(--color-primary)] hover:!bg-[var(--color-primary-hover)] !text-white"
				variant="solid"
				:loading="isProcessing"
			>
				<template #prefix>
					<FeatherIcon name="flag" class="w-4" />
				</template>
				{{ __("End Trip") }}
			</Button>
		</div>
	</div>
</template>

<script setup>
import { ref, computed, inject } from "vue"
import { FeatherIcon, toast } from "frappe-ui"

import { useTripLocation } from "@/composables/useTripLocation"
import { updateTripStatus } from "@/data/deliveryTrips"

const __ = inject("$translate")

const props = defineProps({
	modelValue: {
		type: Object,
		default: null,
	},
})

const emit = defineEmits(["update:modelValue", "tripUpdated"])

const trip = computed(() => props.modelValue)
const isProcessing = ref(false)

const { locationStatus, validateLocation } = useTripLocation()

const detailRows = computed(() => {
	if (!trip.value) return []
	return [
		{ label: "Destination", value: trip.value.lh_destination_city },
		{ label: "Location", value: trip.value.lh_source_city },
		{ label: "Departure Time", value: trip.value.departure_time },
		{ label: "Customer", value: trip.value.lh_customer },
		{ label: "Vehicle", value: trip.value.vehicle },
		{ label: "Driver", value: trip.value.driver_name },
	].filter((row) => row.value)
})

async function handleStartTrip() {
	isProcessing.value = true
	try {
		const canStart = await validateLocation(trip.value.lh_source_map_url)
		if (!canStart) return

		await updateTripStatus(trip.value.name, "In Transit")
		trip.value.status = "In Transit"
		emit("tripUpdated", trip.value)

		toast({
			title: __("Success"),
			text: __("Trip started successfully!"),
			icon: "check-circle",
			position: "bottom-center",
			iconClasses: "text-green-500",
		})
	} finally {
		isProcessing.value = false
	}
}

async function handleEndTrip() {
	isProcessing.value = true
	try {
		const canEnd = await validateLocation(trip.value.lh_destination_map_url)
		if (!canEnd) return

		await updateTripStatus(trip.value.name, "Completed")
		trip.value.status = "Completed"
		emit("tripUpdated", trip.value)

		toast({
			title: __("Success"),
			text: __("Trip completed successfully!"),
			icon: "check-circle",
			position: "bottom-center",
			iconClasses: "text-green-500",
		})
	} finally {
		isProcessing.value = false
	}
}
</script>