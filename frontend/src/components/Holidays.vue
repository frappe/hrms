<template>
	<div class="flex flex-col gap-5 w-full">
		<div class="flex flex-row justify-between items-center">
			<div class="text-xl text-gray-800 font-bold">Upcoming Holidays</div>
			<div id="open-holiday-list" class="text-lg text-blue-500 font-medium cursor-pointer">View All</div>
		</div>

		<div class="flex flex-col bg-white rounded-lg">
			<div
				class="flex flex-row flex-start p-4 items-center justify-between border-b"
				v-for="holiday in upcomingHolidays" :key="holiday.holiday_date"
			>
				<div class="flex flex-row items-center gap-3 grow">
					<FeatherIcon name="calendar" class="h-5 w-5 text-gray-500" />
					<div class="text-lg font-normal text-gray-800">{{ holiday.description }}</div>
				</div>
				<div class="text-lg font-bold text-gray-800">{{ holiday.formatted_holiday_date }}</div>
			</div>
		</div>
	</div>

	<ion-modal ref="modal" trigger="open-holiday-list" :initial-breakpoint="1" :breakpoints="[0, 1]">
		<div class="bg-white w-full flex flex-col items-center justify-center pb-5">
			<div class="w-full pt-8 pb-5 border-b text-center">
				<span class="text-gray-900 font-bold text-xl">Holiday List</span>
			</div>
			<div class="w-full flex flex-col items-center justify-center gap-5 p-4">
				<div
					v-for="holiday in holidays.data"
					:key="holiday.holiday_date"
					class="flex flex-row items-center justify-between w-full"
				>
					<div class="flex flex-row items-center gap-3 grow">
						<FeatherIcon name="calendar" class="h-5 w-5 text-gray-500" />
						<div class="text-lg font-normal text-gray-800">{{ holiday.description }}</div>
					</div>
					<div class="text-lg font-bold text-gray-800">{{ holiday.formatted_holiday_date }}</div>
					</div>
			</div>
		</div>
	</ion-modal>
</template>

<script setup>

import { inject, computed } from "vue"
import { IonModal } from "@ionic/vue"
import { FeatherIcon, createResource } from "frappe-ui"
import dayjs from "@/utils/dayjs"

const employee = inject("$employee")

const holidays = createResource({
	url: "hrms.api.get_holidays_for_employee",
	params: {
		employee: employee.data.name
	},
	auto: true,
	transform: (data) => {
		return data.map((holiday) => {
			holiday.formatted_holiday_date = dayjs(holiday.holiday_date).format("D MMM")
			return holiday
		})
	}
})

const upcomingHolidays = computed(() => {
	const filteredHolidays = holidays.data?.filter((holiday) => {
		return dayjs(holiday.holiday_date).isAfter(dayjs())
	})

	// show only 5 upcoming holidays
	return filteredHolidays?.slice(0, 5)
})

</script>