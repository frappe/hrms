<template>
	<BaseLayout>
		<template #body>
			<div class="flex flex-col items-center my-7 p-4 gap-7 bg-[#fbf6f1]">
				<div class="w-full grid grid-cols-2 gap-4">
					<router-link
						v-for="link in quickLinks"
						:key="link.route"
						:to="{ name: link.route }"
						class="flex flex-col items-center justify-center gap-3 rounded-2xl p-5 bg-[#eef3f8] border border-[#d9e7f8] shadow-sm transition-colors hover:bg-[#d0e0f2] active:bg-[#d0e0f2]"
					>
						<div
							class="flex items-center justify-center w-12 h-12 rounded-full bg-[#d0e0f2] text-[#0062a3]"
						>
							<component :is="link.icon" class="w-6 h-6" />
						</div>
						<span class="text-sm font-medium text-[#0062a3] text-center">
							{{ link.title }}
						</span>
					</router-link>
				</div>

				<TodayTrips />

				<RequestPanel />
			</div>
		</template>
	</BaseLayout>
</template>

<script setup>
import { inject, markRaw } from "vue"

import BaseLayout from "@/components/BaseLayout.vue"
import RequestPanel from "@/components/RequestPanel.vue"
import TodayTrips from "@/components/TodayTrips.vue"
import ExpenseIcon from "@/components/icons/ExpenseIcon.vue"
import DeliveryTripIcon from "@/components/icons/DeliveryTripIcon.vue"

const __ = inject("$translate")

const quickLinks = [
	{
		icon: markRaw(DeliveryTripIcon),
		title: __("Delivery Trip"),
		route: "DeliveryTripDashboard",
	},
	{
		icon: markRaw(ExpenseIcon),
		title: __("Claim an Expense"),
		route: "ExpenseClaimFormView",
	},
]
</script>