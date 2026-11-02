<template>
	<span
		class="inline-flex size-3.5 shrink-0 items-center justify-center rounded-1 border border-current"
		:class="{ 'border-dashed': state === 'skipped' }"
	>
		<LucideCheck v-if="state === 'done'" class="size-2.5" stroke-width="3" />
		<span v-else-if="state === 'in_progress'" class="size-1 rounded-full bg-current" />
		<span v-else-if="state === 'stuck'" class="text-[10px] font-semibold leading-none">!</span>
	</span>
</template>

<script setup>
import LucideCheck from "~icons/lucide/check";

defineProps({
	state: { type: String, default: "pending" },
});
</script>
