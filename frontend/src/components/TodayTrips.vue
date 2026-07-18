<template>
	<div class="flex flex-col w-full gap-3">
		<div class="text-lg text-[var(--color-primary)] font-bold">
			{{ __("Today's Trips") }}
		</div>

		<div
			class="flex flex-col bg-[var(--color-surface)] rounded overflow-auto"
			v-if="trips.length"
		>
			<div
				class="flex flex-row p-3.5 items-center justify-between border-b cursor-pointer"
				v-for="trip in trips"
				:key="trip.name"
				@click="$emit('openTrip', trip)"
			>
				<DeliveryTripItem :doc="trip" />
			</div>
		</div>
		<EmptyState v-else :message="__('No trips scheduled for today')" />
	</div>
</template>

<script setup>
import { ref, onMounted, inject } from "vue"

import DeliveryTripItem from "@/components/DeliveryTripItem.vue"
import EmptyState from "@/components/EmptyState.vue"
import { fetchTodayTrips } from "@/data/deliveryTrips"

const __ = inject("$translate")

defineEmits(["openTrip"])

const trips = ref([])

onMounted(async () => {
	trips.value = await fetchTodayTrips()
})
</script>