<template>
	<nav class="px-2 py-4">
		<router-link
			v-for="item in menuItems"
			:key="item.title"
			:to="item.route"
			v-slot="{ href }"
		>
			<ion-menu-toggle>
				<a
					:href="href"
					class="flex flex-row rounded-lg gap-3 flex-start py-4 px-2 items-center text-gray-700 hover:bg-gray-100 hover:text-gray-900"
				>
					<FeatherIcon :name=item.icon class="h-5 w-5 text-gray-500" />
					<div class="text-base font-normal text-gray-800">{{ item.title }}</div>
				</a>
			</ion-menu-toggle>
		</router-link>
	</nav>
</template>

<script setup>
import { IonMenuToggle } from "@ionic/vue"
import { FeatherIcon } from "frappe-ui"

const menuItems = [
	{
		icon: "home",
		title: "Home",
		route: {
			name: "Home",
		}
	},
	{
		icon: "calendar",
		title: "Leaves",
		route: {
			name: "Leaves",
		}
	},
	{
		icon: "check-circle",
		title: "Attendance",
		route: {
			name: "Home",
		}
	},
	{
		icon: "dollar-sign",
		title: "Expense Claims",
		route: {
			name: "Home",
		}
	},
	{
		icon: "info",
		title: "Payment Information",
		route: {
			name: "Home",
		}
	}
]

</script>