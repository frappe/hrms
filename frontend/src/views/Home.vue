<template>
	<BaseLayout
		:pageTitle="`Hey, ${user?.data?.first_name}!`"
		:showCheckInPanel="true"
	>
		<template #body>
			<div class="flex flex-col items-center mt-3 p-4 gap-7">
				<QuickLinks :items="quickLinks" title="Quick Links" />
				<RequestPanel />
			</div>
		</template>
	</BaseLayout>
</template>

<script setup>
import QuickLinks from "@/components/QuickLinks.vue"
import BaseLayout from "@/components/BaseLayout.vue"
import RequestPanel from "@/components/RequestPanel.vue"

import { inject } from "vue"

const user = inject("$user")

const quickLinks = [
	{
		icon: "calendar",
		title: "Request Leave",
		route: "LeaveApplicationFormView",
	},
	{
		icon: "file-text",
		title: "Claim an Expense",
		route: "ExpenseClaimFormView",
	},
	{
		icon: "dollar-sign",
		title: "Request an Advance",
		route: "EmployeeAdvanceFormView",
	},
	{
		icon: "file",
		title: "Salary Slips",
		route: "SalarySlips",
	},
]
</script>
