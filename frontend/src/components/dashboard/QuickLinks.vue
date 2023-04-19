<template>
	<div class="flex flex-col bg-white rounded-lg">
		<div
			class="flex flex-row flex-start p-4 items-center justify-between border-b"
			v-for="link in quickLinks" :key="link.title"
		>
			<div class="flex flex-row items-center gap-3 grow">
				<FeatherIcon :name=link.icon class="h-5 w-5 text-gray-500" />
				<div class="text-base font-medium text-gray-800">{{ link.title }}</div>
			</div>
			<FeatherIcon name="chevron-right" class="h-5 w-5 text-gray-500" />
		</div>
	</div>
</template>

<script setup>
import { FeatherIcon } from "frappe-ui"

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