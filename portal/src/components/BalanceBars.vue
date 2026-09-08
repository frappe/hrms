<template>
	<div class="flex flex-col gap-3">
		<Progress
			v-for="b in balances"
			:key="b.leave_type"
			:value="b.pct"
			size="md"
			:label="b.leave_type"
		>
			<template #hint>
				<span class="nums text-base font-medium text-ink-gray-5">
					{{ b.balance }} of {{ b.allocated }}
				</span>
			</template>
		</Progress>
		<EmptyState v-if="!balances?.length" message="No leave allocated for this period." />
	</div>
</template>

<script setup>
import { Progress } from "frappe-ui";
import EmptyState from "@/components/EmptyState.vue";

defineProps({ balances: { type: Array, default: () => [] } });
</script>
