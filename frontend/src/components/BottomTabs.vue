<template>
	<ion-tab-bar
		slot="bottom"
		class="bg-white shadow-md sm:w-96 py-2 standalone:pb-safe-bottom"
	>
		<ion-tab-button
			v-for="item in tabItems"
			:key="item.title"
			:tab="item.title"
			:href="item.route"
			:class="[
				'bg-white text-xs space-y-1.5 !hover:border-gray-300 !hover:text-gray-700 transition active:scale-95',
				route.path === item.route
					? 'border-gray-900 text-gray-800 font-semibold'
					: 'text-gray-600 font-normal',
			]"
		>
			<component :is="item.icon" class="h-5 w-5" />
			<div>{{ item.title }}</div>
		</ion-tab-button>
	</ion-tab-bar>
</template>

<script setup>
import { useRoute } from "vue-router"

import { IonTabBar, IonTabButton, IonLabel } from "@ionic/vue"

import HomeIcon from "@/components/icons/HomeIcon.vue"
import LeaveIcon from "@/components/icons/LeaveIcon.vue"
import ExpenseIcon from "@/components/icons/ExpenseIcon.vue"
import SalaryIcon from "@/components/icons/SalaryIcon.vue"

const route = useRoute()

const tabItems = [
	{
		icon: HomeIcon,
		title: "Home",
		route: "/home",
	},
	{
		icon: LeaveIcon,
		title: "Leaves",
		route: "/dashboard/leaves",
	},
	{
		icon: ExpenseIcon,
		title: "Expenses",
		route: "/dashboard/expense-claims",
	},
	{
		icon: SalaryIcon,
		title: "Salary",
		route: "/dashboard/salary-slips",
	},
]
</script>
