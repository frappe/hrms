<template>
	<BaseLayout pageTitle="Leaves &amp; Holidays">
		<template #body>
			<div class="flex flex-col items-center mt-5 gap-7">
				<LeaveBalance />
			</div>
		</template>
	</BaseLayout>
</template>

<script setup>

import BaseLayout from "@/components/BaseLayout.vue"
import LeaveBalance from "@/components/LeaveBalance.vue"

</script>