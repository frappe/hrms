<template>
	<BaseLayout pageTitle="Expense Claims">
		<template #body>
			<div class="flex flex-col mt-5 mb-7 p-4 gap-7">
				<ExpenseClaimSummary />

				<div class="w-full">
					<router-link
						:to="{ name: 'ExpenseClaimFormView' }"
						v-slot="{ navigate }"
					>
						<Button @click="navigate" appearance="primary" class="py-2 w-full">
							Claim an Expense
						</Button>
					</router-link>
				</div>

				<div>
					<div class="text-xl text-gray-800 font-bold">Recent Expenses</div>
					<RequestList
						:component="markRaw(ExpenseClaimItem)"
						:items="myClaims.data"
						:addListButton="true"
						listButtonRoute="ExpenseClaimListView"
					/>
				</div>

				<div>
					<div class="flex flex-row justify-between items-center">
						<div class="text-xl text-gray-800 font-bold">
							Employee Advance Balance
						</div>
						<router-link
							v-if="advanceBalance?.data?.length"
							:to="{ name: 'EmployeeAdvanceListView' }"
							class="text-lg text-blue-500 font-medium cursor-pointer"
						>
							View List
						</router-link>
					</div>

					<EmployeeAdvanceBalance :items="advanceBalance.data" />
				</div>
			</div>
		</template>
	</BaseLayout>
</template>

<script setup>
import { markRaw, inject, onBeforeUnmount, onMounted } from "vue"

import BaseLayout from "@/components/BaseLayout.vue"
import ExpenseClaimSummary from "@/components/ExpenseClaimSummary.vue"
import RequestList from "@/components/RequestList.vue"
import ExpenseClaimItem from "@/components/ExpenseClaimItem.vue"
import EmployeeAdvanceBalance from "@/components/EmployeeAdvanceBalance.vue"

import { myClaims } from "@/data/claims"
import { advanceBalance } from "@/data/advances"

const socket = inject("$socket")
const employee = inject("$employee")

onMounted(() => {
	socket.off("hrms:update_expense_claims")
	socket.on("hrms:update_expense_claims", (data) => {
		if (data.employee === employee().name) {
			myClaims.reload()
		}
	})

	socket.off("hrms:update_employee_advances")
	socket.on("hrms:update_employee_advances", (data) => {
		if (data.employee === employee().name) {
			advanceBalance.reload()
		}
	})
})

onBeforeUnmount(() => {
	socket.off("hrms:update_expense_claims")
	socket.off("hrms:update_employee_advances")
})
</script>
