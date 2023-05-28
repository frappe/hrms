<template>
	<div class="flex flex-col bg-white rounded-lg mt-5 overflow-auto" v-if="items">
		<div
			class="flex flex-row p-3.5 items-center justify-between border-b cursor-pointer"
			v-for="link in props.items" :key="link.name"
		>
			<div class="flex flex-col w-full justify-center gap-2.5">
				<div class="flex flex-row items-center justify-between">
					<div class="flex flex-row items-start gap-3 grow">
						<FeatherIcon name="calendar" class="h-5 w-5 text-gray-500" />
						<div class="flex flex-col items-start">
							<div class="text-lg font-normal text-gray-800">{{ link.leave_type }}</div>
							<div class="text-sm font-normal text-gray-500">
								<span>{{ link.leave_dates }}</span>
								<span class="whitespace-pre"> &middot; </span>
								<span class="whitespace-nowrap">{{ link.total_leave_days }}</span>
							</div>
						</div>
					</div>
					<div class="flex flex-row justify-end items-center gap-2">
						<Badge :colorMap="colorMap" :label="link.status" />
						<FeatherIcon name="chevron-right" class="h-5 w-5 text-gray-500" />
					</div>
				</div>
				<div v-if="props.teamRequests" class="flex flex-row items-center gap-2 pl-8">
					<EmployeeAvatar :employeeID="link.employee"/>
					<div class="text-sm text-gray-600 grow">{{ link.employee_name }}</div>
				</div>
			</div>
		</div>
	</div>
	<div class="text-sm text-gray-500 mt-5 flex flex-col items-center" v-else>You have no requests</div>
</template>

<script setup>

import { FeatherIcon, Badge, Avatar } from "frappe-ui"
import dayjs from "@/utils/dayjs"

import EmployeeAvatar from "@/components/EmployeeAvatar.vue"

const props = defineProps({
	items: {
		type: Array,
	},
	teamRequests: {
		type: Boolean,
		default: false,
	}
})

const colorMap = {
	Approved: "green",
	Rejected: "red",
	Open: "yellow"
}

</script>