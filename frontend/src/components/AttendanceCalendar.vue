<template>
	<div class="flex flex-col w-full gap-5" v-if="calendarEvents.data">
		<div class="flex flex-row justify-between items-center px-4">
			<Button
				icon="chevron-left"
				variant="ghost"
				@click="firstOfMonth = firstOfMonth.subtract(1, 'M')"
			/>

			<span class="text-lg text-gray-800 font-bold">
				{{ firstOfMonth.format("MMMM") }} {{ firstOfMonth.format("YYYY") }}
			</span>
			<Button
				icon="chevron-right"
				variant="ghost"
				@click="firstOfMonth = firstOfMonth.add(1, 'M')"
			/>
		</div>

		<div class="flex flex-col gap-4 bg-white py-3 px-3.5 rounded-lg border-none">
			<div class="grid grid-cols-3 gap-y-3">
				<div v-for="[status, color] of Object.entries(colorMap)" class="flex flex-col gap-1">
					<div class="flex flex-row gap-1 items-center">
						<span class="text-gray-600 text-sm font-medium leading-5"> {{ status }} </span>
						<FeatherIcon name="check-circle" :class="`text-${color}-500 h-3 w-3`" />
					</div>
					<span class="text-gray-800 text-base font-semibold leading-6">
						{{ summary[status] || 0 }}
					</span>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { FeatherIcon } from "frappe-ui"
import { computed, inject, ref } from "vue"

import { calendarEvents } from "@/data/attendance"

const dayjs = inject("$dayjs")

const firstOfMonth = ref(dayjs().date(1).startOf("D"))

const colorMap = {
	Present: "green",
	WFH: "yellow",
	"Half Day": "orange",
	Absent: "red",
	"On Leave": "blue",
	Holiday: "gray",
}

const summary = computed(() => {
	const summary = {}

	for (const status of Object.values(calendarEvents.data)) {
		if (status in summary) {
			summary[status] += 1
		} else {
			summary[status] = 1
		}
	}

	return summary
})
</script>
