<template>
	<div class="flex flex-col w-full gap-5" v-if="summary">
		<div class="text-lg text-[var(--color-primary)] font-bold">
			{{ __("Delivery Trips Summary") }}
		</div>
		<div class="grid grid-cols-2 gap-3">
			<div
				v-for="stat in statusCards"
				:key="stat.status"
				class="flex flex-col gap-1.5 bg-[var(--color-card-bg)] border border-[var(--color-card-border)] rounded-lg py-3 px-3.5"
			>
				<div class="flex flex-row items-center gap-1.5">
					<FeatherIcon :name="stat.icon" class="h-3.5 w-3.5" :class="stat.iconClass" />
					<span class="text-[var(--color-text-muted)] text-sm font-medium leading-5">
						{{ __(stat.status) }}
					</span>
				</div>
				<span class="text-[var(--color-primary)] text-xl font-bold leading-6">
					{{ summary[stat.status] ?? 0 }}
				</span>
			</div>
		</div>
	</div>
</template>

<script setup>
import { ref, onMounted } from "vue"
import { FeatherIcon } from "frappe-ui"
import { inject } from "vue"

import { fetchTripsSummary } from "@/data/deliveryTrips"

const __ = inject("$translate")

const summary = ref(null)

const statusCards = [
	{ status: "Scheduled", icon: "clock", iconClass: "text-[var(--color-blue-muted)]" },
	{ status: "In Transit", icon: "truck", iconClass: "text-[var(--color-primary)]" },
	{ status: "Completed", icon: "check-circle", iconClass: "text-green-500" },
	{ status: "Cancelled", icon: "x-circle", iconClass: "text-red-500" },
]

onMounted(async () => {
	summary.value = await fetchTripsSummary()
})
</script>