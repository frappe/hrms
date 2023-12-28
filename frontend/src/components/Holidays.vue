<template>
	<div class="flex flex-col gap-5 w-full">
		<div class="flex flex-row justify-between items-center">
			<div class="text-lg text-gray-800 font-bold">Upcoming Holidays</div>
			<div
				v-if="holidays?.data?.length"
				id="open-holiday-list"
				class="text-sm text-gray-800 font-semibold cursor-pointer underline underline-offset-2"
			>
				View All
			</div>
		</div>

		<div class="flex flex-col bg-white rounded" v-if="upcomingHolidays?.length">
			<div
				class="flex flex-row flex-start p-4 items-center justify-between border-b"
				v-for="holiday in upcomingHolidays"
				:key="holiday.holiday_date"
			>
				<div class="flex flex-row items-center gap-3 grow">
					<FeatherIcon name="calendar" class="h-5 w-5 text-gray-500" />
					<div class="text-base font-normal text-gray-800">
						{{ holiday.description }}
					</div>
				</div>
				<div class="text-base font-bold text-gray-800">
					{{ holiday.formatted_holiday_date }}
				</div>
			</div>
		</div>

		<EmptyState message="You have no upcoming holidays" v-else />
	</div>

	<ion-modal
		ref="modal"
		v-if="holidays?.data?.length"
		trigger="open-holiday-list"
		:initial-breakpoint="1"
		:breakpoints="[0, 1]"
	>
		<div class="bg-white w-full flex flex-col items-center justify-center pb-5">
			<div class="w-full pt-8 pb-5 border-b text-center">
				<span class="text-gray-900 font-bold text-lg">Holiday List</span>
			</div>
			<div class="w-full flex flex-col items-center justify-center gap-5 p-4">
				<div
					v-for="holiday in holidays.data"
					:key="holiday.holiday_date"
					class="flex flex-row items-center justify-between w-full"
				>
					<div class="flex flex-row items-center gap-3 grow">
						<FeatherIcon name="calendar" class="h-5 w-5 text-gray-500" />
						<div class="text-base font-normal text-gray-800">
							{{ holiday.description }}
						</div>
					</div>
					<div
						:class="[
							'text-base font-bold',
							holiday.is_upcoming ? 'text-gray-800' : 'text-gray-500',
						]"
					>
						{{ holiday.formatted_holiday_date }}
					</div>
				</div>
			</div>
		</div>
	</ion-modal>
</template>

<script setup>
import { inject, computed } from "vue"
import { IonModal } from "@ionic/vue"
import { FeatherIcon, createResource } from "frappe-ui"

const employee = inject("$employee")
const dayjs = inject("$dayjs")

const holidays = createResource({
	url: "hrms.api.get_holidays_for_employee",
	params: {
		employee: employee.data.name,
	},
	auto: true,
	transform: (data) => {
		return data.map((holiday) => {
			const holidayDate = dayjs(holiday.holiday_date)
			holiday.is_upcoming = holidayDate.isAfter(dayjs())
			holiday.formatted_holiday_date = holidayDate.format("ddd, D MMM YYYY")
			return holiday
		})
	},
})

const upcomingHolidays = computed(() => {
	const filteredHolidays = holidays.data?.filter(
		(holiday) => holiday.is_upcoming
	)

	// show only 5 upcoming holidays
	return filteredHolidays?.slice(0, 5)
})
</script>
