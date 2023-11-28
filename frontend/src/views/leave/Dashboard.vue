<template>
	<BaseLayout pageTitle="Leaves &amp; Holidays">
		<template #body>
			<div class="flex flex-col items-center mt-7 mb-7 py-4">
				<LeaveBalance />

				<div class="flex flex-col gap-7 mt-5 px-4 w-full">
					<router-link
						:to="{ name: 'LeaveApplicationFormView' }"
						v-slot="{ navigate }"
					>
						<Button
							@click="navigate"
							variant="solid"
							class="py-5 text-base w-full"
						>
							Request a Leave
						</Button>
					</router-link>
					<div>
						<div class="text-lg text-gray-800 font-bold">Recent Leaves</div>
						<RequestList
							:component="markRaw(LeaveRequestItem)"
							:items="myLeaves.data"
							:addListButton="true"
							listButtonRoute="LeaveApplicationListView"
						/>
					</div>
					<Holidays />
				</div>
			</div>
		</template>
	</BaseLayout>
</template>

<script setup>
import { inject, onMounted, onBeforeUnmount, markRaw } from "vue"

import BaseLayout from "@/components/BaseLayout.vue"
import LeaveBalance from "@/components/LeaveBalance.vue"
import RequestList from "@/components/RequestList.vue"
import LeaveRequestItem from "@/components/LeaveRequestItem.vue"
import Holidays from "@/components/Holidays.vue"

import { myLeaves } from "@/data/leaves"

const socket = inject("$socket")
const employee = inject("$employee")

onMounted(() => {
	socket.on("hrms:update_leaves", (data) => {
		if (data.employee === employee.data.name) {
			myLeaves.reload()
		}
	})
})

onBeforeUnmount(() => {
	socket.off("hrms:update_leaves")
})
</script>
