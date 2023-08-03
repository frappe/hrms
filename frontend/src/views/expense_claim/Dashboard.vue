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
						:items="myRequests.data"
						:addListButton="true"
						listButtonRoute="ExpenseClaimListView"
					/>
				</div>

				<div>
					<div class="text-xl text-gray-800 font-bold">
						Employee Advance Balance
					</div>
					<EmployeeAdvanceBalance :items="advanceBalance.data" />
				</div>
			</div>
		</template>
	</BaseLayout>
</template>

<script setup>
import BaseLayout from "@/components/BaseLayout.vue"
import ExpenseClaimSummary from "@/components/ExpenseClaimSummary.vue"
import RequestList from "@/components/RequestList.vue"
import EmployeeAdvanceBalance from "@/components/EmployeeAdvanceBalance.vue"

import { myRequests } from "@/data/claims"
import { advanceBalance } from "@/data/advances"
</script>
