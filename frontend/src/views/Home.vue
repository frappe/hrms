<template>
	<BaseLayout :pageTitle="`Hey, ${ user?.data?.first_name }!`">
		<template #content>
			<!-- quick links -->
			<div class="flex flex-col gap-5 mt-4 p-4">
				<div class="font-medium text-gray-900">Quick Links</div>
				<QuickLinks />
			</div>
		</template>
	</BaseLayout>
</template>

<script setup>

import QuickLinks from "@/components/QuickLinks.vue"
import BaseLayout from "@/components/BaseLayout.vue"

import { inject } from "vue"

const user = inject("$user")

</script>