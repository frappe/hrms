<template>
	<aside
		class="hidden md:flex flex-col w-64 shrink-0 border-r border-gray-200 bg-white h-full overflow-hidden"
	>
		<!-- Branding -->
		<div class="px-5 py-4 border-b border-gray-100 flex items-center gap-3">
			<FrappeHRLogo class="h-8 w-8" />
			<span class="text-base font-semibold text-gray-900">Frappe HR</span>
		</div>

		<!-- User info -->
		<div class="px-4 py-3 border-b border-gray-100 flex items-center gap-3">
			<router-link :to="{ name: 'Profile' }">
				<Avatar
					:image="user.data.user_image"
					:label="user.data.first_name"
					size="xl"
				/>
			</router-link>
			<div class="min-w-0 flex-1">
				<p class="text-sm font-medium text-gray-900 truncate">{{ user.data.full_name }}</p>
				<p v-if="employee.data.designation" class="text-xs text-gray-500 truncate">
					{{ employee.data.designation }}
				</p>
			</div>
			<router-link :to="{ name: 'Notifications' }" class="relative ml-auto shrink-0">
				<FeatherIcon name="bell" class="h-5 w-5 text-gray-500 hover:text-gray-700" />
				<span
					v-if="unreadNotificationsCount.data"
					class="absolute -top-0.5 -right-0.5 h-2 w-2 bg-red-500 rounded-full border border-white"
				/>
			</router-link>
		</div>

		<!-- Navigation -->
		<nav class="flex-1 overflow-y-auto px-3 py-3">
			<template v-for="item in navItems" :key="item.route ?? item.label">
				<!-- Section header -->
				<p
					v-if="item.type === 'section'"
					class="px-3 pt-4 pb-1.5 text-xs font-semibold text-gray-400 uppercase tracking-wider"
				>
					{{ item.label }}
				</p>

				<!-- Nav link -->
				<router-link
					v-else
					:to="{ name: item.route }"
					class="flex items-center gap-3 px-3 py-2.5 mb-0.5 rounded-lg text-sm font-medium transition-colors"
					:class="
						isActive(item)
							? 'bg-gray-100 text-gray-900'
							: 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
					"
				>
					<component :is="item.icon" class="h-4 w-4 shrink-0" />
					{{ __(item.title) }}
				</router-link>
			</template>
		</nav>

		<!-- Footer -->
		<div class="border-t border-gray-100 px-3 py-3">
			<router-link
				:to="{ name: 'Profile' }"
				class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-50 hover:text-gray-900 transition-colors"
			>
				<FeatherIcon name="settings" class="h-4 w-4 shrink-0" />
				{{ __("Settings") }}
			</router-link>
		</div>
	</aside>
</template>

<script setup>
import { inject, markRaw } from "vue"
import { useRoute } from "vue-router"
import { FeatherIcon, Avatar } from "frappe-ui"

import FrappeHRLogo from "@/components/icons/FrappeHRLogo.vue"
import HomeIcon from "@/components/icons/HomeIcon.vue"
import TimerIcon from "@/components/icons/TimerIcon.vue"
import TimesheetIcon from "@/components/icons/TimesheetIcon.vue"
import LeaveIcon from "@/components/icons/LeaveIcon.vue"
import ExpenseIcon from "@/components/icons/ExpenseIcon.vue"
import SalaryIcon from "@/components/icons/SalaryIcon.vue"

import { unreadNotificationsCount } from "@/data/notifications"

const route = useRoute()
const __ = inject("$translate")
const user = inject("$user")
const employee = inject("$employee")

const navItems = [
	{ icon: markRaw(HomeIcon),       title: "Home",            route: "Home",                    path: "/home" },
	{ type: "section", label: "Timesheets" },
	{ icon: markRaw(TimerIcon),      title: "Start Timer",     route: "TimesheetTimer",          path: "/timesheets/timer", exact: true },
	{ icon: markRaw(TimesheetIcon),  title: "My Timesheets",   route: "TimesheetListView",       path: "/timesheets" },
	{ type: "section", label: "HR" },
{ icon: markRaw(LeaveIcon),      title: "Leaves",          route: "LeavesDashboard",         path: "/dashboard/leaves" },
	{ icon: markRaw(ExpenseIcon),    title: "Expenses",        route: "ExpenseClaimsDashboard",  path: "/dashboard/expense-claims" },
	{ icon: markRaw(SalaryIcon),     title: "Salary Slips",    route: "SalarySlipsDashboard",   path: "/dashboard/salary-slips" },
]

function isActive(item) {
	if (item.exact) return route.path === item.path
	// prefix match — but don't let /timesheets match /timesheets/timer
	if (route.path === item.path) return true
	if (item.path && route.path.startsWith(item.path + "/")) {
		// exclude exact child routes that have their own nav entry
		const exactChildren = navItems.filter((n) => n.exact).map((n) => n.path)
		if (exactChildren.some((p) => route.path === p)) return false
		return true
	}
	return false
}
</script>
