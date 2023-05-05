<template>
	<BaseLayout pageTitle="Profile">
		<template #body>
			<div class="flex flex-col items-center mt-5 p-4">
				<img
					class="h-24 w-24 rounded-full object-cover"
					:src="user.data.user_image"
					:alt="user.data.first_name"
				/>

				<div class="flex flex-col gap-1 items-center mt-2 mb-5">
					<span v-if="employee" class="text-xl font-bold text-gray-900">{{ employee?.data?.employee_name }}</span>
					<span v-if="employee" class="font-normal text-sm text-gray-500">{{ employee?.data?.designation }}</span>
				</div>

				<QuickLinks title="Profile" :items="profileLinks" />
				<QuickLinks title="Documents" :items="documentLinks" />

				<Button @click="logout" appearance="white" class="text-red-500 w-full shadow py-2 mt-5" icon-left="log-out"> Log Out </Button>
			</div>
		</template>
	</BaseLayout>
</template>

<script setup>

import QuickLinks from "@/components/QuickLinks.vue"
import BaseLayout from "@/components/BaseLayout.vue"

import { inject } from "vue"

import { showErrorAlert } from "@/utils.js"

const session = inject("$session")
const user = inject("$user")
const employee = inject("$employee")

const profileLinks = [
	{
		icon: "user",
		title: "Personal Information",
	},
	{
		icon: "bell",
		title: "Notification Settings",
	},
	{
		icon: "zap",
		title: "My Journey",
	}
]

const documentLinks = [
	{
		icon: "dollar-sign",
		title: "Tax Deductions",
	},
	{
		icon: "hard-drive",
		title: "Personal Documents",
	},
	{
		icon: "file",
		title: "Company Policies",
	}
]

const logout = async () => {
	try {
		await session.logout.submit()
	} catch (e) {
		const msg = "An error occurred while attempting to log out!";
		console.error(msg, e)
		showErrorAlert(msg)
	}
}

</script>