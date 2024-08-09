<template>
	<div class="flex flex-col w-full">
		<div class="flex flex-row justify-between items-center px-4">
			<div class="text-lg text-gray-800 font-bold">Attendance Calendar</div>
		</div>

		<div class="flex flex-row gap-4 overflow-x-auto py-2 mt-3" v-if="calendarEvents.data"></div>

		<EmptyState message="You have no leaves allocated" v-else />
	</div>
</template>

<script setup>
import { calendarEvents } from "@/data/attendance"
</script>
