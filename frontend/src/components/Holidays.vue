<template>
	<div class="flex flex-col gap-5 w-full">
		<div class="flex flex-row justify-between items-center">
			<div class="text-xl text-gray-800 font-bold">Upcoming Holidays</div>
			<div class="text-lg text-blue-500 font-medium cursor-pointer">View All</div>
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
</template>

<script setup>

import { inject, computed } from "vue"
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
	return holidays.data.filter((holiday) => {
		return dayjs(holiday.holiday_date).isAfter(dayjs())
	})
})

</script>