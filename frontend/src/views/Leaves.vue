<template>
	<BaseLayout pageTitle="Leaves &amp; Holidays">
		<template #body>
			<div class="flex flex-col items-center mt-5 mb-7">
				<LeaveBalance />

				<div class="flex flex-col gap-7 px-4 mt-4 w-full">
					<Button appearance="primary" class="py-2 w-full">Request a Leave</Button>
					<div>
						<div class="text-xl text-gray-800 font-bold">Leaves This Month</div>
						<RequestList :items="leavesThisMonth" />
					</div>
					<Holidays />
				</div>
			</div>
		</template>
	</BaseLayout>
</template>

<script setup>

import BaseLayout from "@/components/BaseLayout.vue"
import LeaveBalance from "@/components/LeaveBalance.vue"
import RequestList from "@/components/RequestList.vue"
import Holidays from "@/components/Holidays.vue"

import { leavesThisMonth } from "@/data/leaves"

</script>