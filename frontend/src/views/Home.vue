<template>
	<BaseLayout :pageTitle="`Hey, ${ user?.data?.first_name }!`" :showCheckInPanel="true">
		<template #body>
			<div class="flex flex-col items-center mt-5 p-4 gap-7">
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
	},
	{
		icon: "dollar-sign",
		title: "Claim an Expense",
	},
	{
		icon: "file",
		title: "Payslip",
	},
	{
		icon: "hard-drive",
		title: "Documents",
	}
]

</script>