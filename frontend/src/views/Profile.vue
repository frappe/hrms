<template>
	<BaseLayout pageTitle="Profile">
		<template #body>
			<div class="flex flex-col items-center mt-5 p-4 gap-5">
				<Avatar :imageURL="user.data.user_image" :label="user.data.first_name" size="lg" />
				<Button @click="logout" appearance="white" class="text-red-500 w-full shadow py-2" icon-left="log-out"> Log Out </Button>
			</div>
		</template>
	</BaseLayout>
</template>

<script setup>

import { Avatar } from "frappe-ui"

import QuickLinks from "@/components/QuickLinks.vue"
import BaseLayout from "@/components/BaseLayout.vue"

import { inject } from "vue"

import { showErrorAlert } from "@/utils.js"

const employee = inject("$employee")
const user = inject("$user")
const session = inject("$session")

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