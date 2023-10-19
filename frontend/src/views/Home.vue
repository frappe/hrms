<template>
	<BaseLayout>
		<template #body>
			<div class="flex flex-col items-center my-7 p-4 gap-7">
				<CheckInPanel />
				<QuickLinks :items="quickLinks" title="Quick Links" />
				<RequestPanel />
			</div>
		</template>
	</BaseLayout>
</template>

<script setup>
import CheckInPanel from "@/components/CheckInPanel.vue"
import QuickLinks from "@/components/QuickLinks.vue"
import BaseLayout from "@/components/BaseLayout.vue"
import RequestPanel from "@/components/RequestPanel.vue"

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
