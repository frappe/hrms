<script setup>
// One row of a list card, such as a document or an asset: an icon, a title with details under
// it, a status badge and actions. On a phone the badge moves under the title, so the actions
// keep their room.
defineProps({
	icon: { type: String, required: true },
});
</script>

<template>
	<div
		class="relative flex items-center gap-3 rounded-4 px-3 py-2.5 before:pointer-events-none before:absolute before:inset-x-3 before:-top-px before:border-t before:border-outline-gray-1 first:before:hidden"
	>
		<span :class="icon" class="size-4 shrink-0 text-ink-gray-5" aria-hidden="true" />
		<div class="min-w-0 flex-1">
			<div class="truncate text-base text-ink-gray-8"><slot /></div>
			<slot name="details" />
			<div v-if="$slots.badge" class="mt-1.5 flex sm:hidden"><slot name="badge" /></div>
		</div>
		<div v-if="$slots.badge" class="hidden shrink-0 sm:flex"><slot name="badge" /></div>
		<div v-if="$slots.actions" class="flex shrink-0 items-center gap-1">
			<slot name="actions" />
		</div>
	</div>
</template>
