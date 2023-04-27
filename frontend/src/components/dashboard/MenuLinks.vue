<template>
	<nav class="px-2 py-4 flex flex-col gap-1" v-if="currentRoute">
		<router-link
			v-for="item in menuItems"
			:key="item.title"
			:to="item.route"
			v-slot="{ href }"
		>
			<ion-menu-toggle>
				<a
					:href="href"
					:class="[
						item.current
							? 'bg-gray-200 font-bold text-gray-800'
							: 'text-gray-700 font-normal hover:bg-gray-100 hover:text-gray-900',
						'flex flex-row rounded-lg gap-3 flex-start py-3 px-2 items-center text-base',
					]"
				>
					<FeatherIcon :name=item.icon class="h-5 w-5" />
					<div>{{ item.title }}</div>
				</a>
			</ion-menu-toggle>
		</router-link>
	</nav>
</template>

<script setup>
import { IonMenuToggle } from "@ionic/vue"
import { FeatherIcon } from "frappe-ui"

import { computed, ref } from "vue"
import { useRoute } from "vue-router"

const menuItems = ref([
	{
		icon: "home",
		title: "Home",
		route: {
			name: "Home",
		},
		current: false
	},
	{
		icon: "calendar",
		title: "Leaves",
		route: {
			name: "Leaves",
		},
		current: false
	},
	{
		icon: "check-circle",
		title: "Attendance",
		route: {
			name: "Login",
		},
		current: false
	},
	{
		icon: "dollar-sign",
		title: "Expense Claims",
		route: {
			name: "Login",
		},
		current: false
	},
	{
		icon: "info",
		title: "Payment Information",
		route: {
			name: "Login",
		},
		current: false
	}
])

const route = useRoute()
const currentRoute = computed(() => {
	menuItems.value.forEach((item) => {
		item.current = item.route.name === route.name
	})
	return route.name
})

</script>