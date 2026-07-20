<template>
	<div
		slot="bottom"
		class="mx-auto mb-3 w-[calc(100%-1.5rem)] max-w-[360px] overflow-hidden rounded-xl border border-outline-gray-2 bg-surface-white shadow-md"
	>
		<MobileNav class="w-full !border-t-0">
			<MobileNavItem
				v-for="item in tabItems"
				:key="item.title"
				:label="item.title"
				:icon="item.icon"
				:to="item.route"
				:active="isActive(item.route)"
			/>
		</MobileNav>
	</div>
</template>

<script setup>
import { useRoute } from "vue-router"
import { MobileNav, MobileNavItem } from "frappe-ui"

import HomeIcon from "@/components/icons/HomeIcon.vue"
import LeaveIcon from "@/components/icons/LeaveIcon.vue"
import ExpenseIcon from "@/components/icons/ExpenseIcon.vue"
import SalaryIcon from "@/components/icons/SalaryIcon.vue"
import AttendanceIcon from "@/components/icons/AttendanceIcon.vue"
import { inject } from "vue"

const __ = inject("$translate")

const route = useRoute()
const isActive = (itemRoute) =>
	route.path === itemRoute || route.path.startsWith(`${itemRoute}/`)

const tabItems = [
	{
		icon: HomeIcon,
		title: __("Home"),
		route: "/home",
	},
	{
		icon: AttendanceIcon,
		title: __("Attendance"),
		route: "/dashboard/attendance",
	},
	{
		icon: LeaveIcon,
		title: __("Leaves"),
		route: "/dashboard/leaves",
	},
	{
		icon: ExpenseIcon,
		title: __("Expenses"),
		route: "/dashboard/expense-claims",
	},
	{
		icon: SalaryIcon,
		title: __("Salary"),
		route: "/dashboard/salary-slips",
	},
]
</script>
