<template>
	<BaseLayout pageTitle="Expense Claims">
		<template #body>
			<div class="flex flex-col mt-7 mb-7 p-4 gap-7">
				<ExpenseClaimSummary />

				<div class="w-full">
					<router-link
						:to="{ name: 'ExpenseClaimFormView' }"
						v-slot="{ navigate }"
					>
						<Button
							@click="navigate"
							variant="solid"
							class="w-full py-5 text-base"
						>
							Claim an Expense
						</Button>
					</router-link>
				</div>

				<div>
					<div class="text-lg text-gray-800 font-bold">Recent Expenses</div>
					<RequestList
						:component="markRaw(ExpenseClaimItem)"
						:items="myClaims.data"
						:addListButton="true"
						listButtonRoute="ExpenseClaimListView"
					/>
				</div>

				<div>
					<div class="flex flex-row justify-between items-center">
						<div class="text-lg text-gray-800 font-bold">
							Employee Advance Balance
						</div>
						<router-link
							:to="{ name: 'EmployeeAdvanceListView' }"
							class="text-sm text-gray-800 font-semibold cursor-pointer underline underline-offset-2"
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
import { markRaw } from "vue"

import BaseLayout from "@/components/BaseLayout.vue"
import ExpenseClaimSummary from "@/components/ExpenseClaimSummary.vue"
import RequestList from "@/components/RequestList.vue"
import ExpenseClaimItem from "@/components/ExpenseClaimItem.vue"
import EmployeeAdvanceBalance from "@/components/EmployeeAdvanceBalance.vue"

import { myClaims } from "@/data/claims"
import { advanceBalance } from "@/data/advances"
</script>
