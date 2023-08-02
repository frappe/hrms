<template>
	<BaseLayout pageTitle="Leaves &amp; Holidays">
		<template #body>
			<div class="flex flex-col items-center mt-5 mb-7">
				<LeaveBalance />

				<div class="flex flex-col gap-7 px-4 mt-4 w-full">
					<router-link
						:to="{ name: 'LeaveApplicationFormView' }"
						v-slot="{ navigate }"
					>
						<Button @click="navigate" appearance="primary" class="py-2 w-full">
							Request a Leave
						</Button>
					</router-link>
					<div>
						<div class="text-xl text-gray-800 font-bold">Leaves This Month</div>
						<RequestList :items="leavesThisMonth" />
					</div>
					<Holidays />
				</div>
			</div>
		</template>
	</BaseLayout>
</template>

<script setup>
import { inject, onUnmounted } from "vue"

import BaseLayout from "@/components/BaseLayout.vue"
import LeaveBalance from "@/components/LeaveBalance.vue"
import RequestList from "@/components/RequestList.vue"
import Holidays from "@/components/Holidays.vue"

import { leavesThisMonth, myRequests } from "@/data/leaves"

const socket = inject("$socket")
const employee = inject("$employee")

socket.on("hrms:update_leaves", (data) => {
	if (data.employee === employee.data.name) {
		myRequests.reload()
	}
})

onUnmounted(() => {
	socket.off("hrms:update_leaves")
})
</script>
