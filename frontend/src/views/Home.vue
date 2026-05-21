<template>
	<BaseLayout>
		<template #body>
			<div class="flex flex-col items-center my-7 p-4 gap-7">
				<QuickLinks :items="quickLinks" :title="__('Quick Links')" />
				<RequestPanel />
			</div>
		</template>
	</BaseLayout>
</template>

<script setup>
import { inject, markRaw } from "vue"

import QuickLinks from "@/components/QuickLinks.vue"
import BaseLayout from "@/components/BaseLayout.vue"
import RequestPanel from "@/components/RequestPanel.vue"
import LeaveIcon from "@/components/icons/LeaveIcon.vue"
import ExpenseIcon from "@/components/icons/ExpenseIcon.vue"
import EmployeeAdvanceIcon from "@/components/icons/EmployeeAdvanceIcon.vue"
import SalaryIcon from "@/components/icons/SalaryIcon.vue"
import TimesheetIcon from "@/components/icons/TimesheetIcon.vue"

const __ = inject("$translate")

const quickLinks = [
	{
		icon: markRaw(LeaveIcon),
		title: __("Request Leave"),
		route: "LeaveApplicationFormView",
	},
	{
		icon: markRaw(ExpenseIcon),
		title: __("Claim an Expense"),
		route: "ExpenseClaimFormView",
	},
	{
		icon: markRaw(EmployeeAdvanceIcon),
		title: __("Request an Advance"),
		route: "EmployeeAdvanceFormView",
	},
	{
		icon: markRaw(SalaryIcon),
		title: __("View Salary Slips"),
		route: "SalarySlipsDashboard",
	},
	{
		icon: markRaw(TimesheetIcon),
		title: __("My Timesheets"),
		route: "TimesheetListView",
	},
]
</script>
