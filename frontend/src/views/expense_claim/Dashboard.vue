<template>
	<BaseLayout pageTitle="Expense Claims">
		<template #body>
			<div class="flex flex-col items-center mt-5 mb-7 p-4 gap-7">
				<ExpenseClaimSummary />

				<div class="w-full">
					<router-link
						:to="{ name: 'ExpenseClaimFormView' }"
						v-slot="{ navigate }"
					>
						<Button @click="navigate" appearance="primary" class="py-2 w-full">
							Claim an Expense
						</Button>
					</router-link>
				</div>
			</div>
		</template>
	</BaseLayout>
</template>

<script setup>
import BaseLayout from "@/components/BaseLayout.vue"
import ExpenseClaimSummary from "@/components/ExpenseClaimSummary.vue"
</script>
