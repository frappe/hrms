<script setup>
// One row of a list card, such as a document or an asset: an icon, a title with details under
// it, a status badge and actions. The rows share the card's columns (LIST_CLASS), so badges and
// actions line up from row to row. On a phone the badge moves under the title, so the actions
// keep their room.
defineProps({
	icon: { type: String, required: true },
});
</script>

<script>
// the card around the rows: icon, title, badge (not on a phone) and actions columns
export const LIST_CLASS =
	"grid grid-cols-[auto_minmax(0,1fr)_auto] gap-y-px rounded-6 border border-outline-gray-1 p-1 sm:grid-cols-[auto_minmax(0,1fr)_auto_auto]";
</script>

<template>
	<div
		class="relative col-span-full grid grid-cols-subgrid items-center gap-x-3 rounded-4 px-3 py-2.5 before:pointer-events-none before:absolute before:inset-x-3 before:-top-px before:border-t before:border-outline-gray-1 first:before:hidden"
	>
		<span :class="icon" class="size-4 shrink-0 text-ink-gray-5" aria-hidden="true" />
		<div class="min-w-0 flex-1">
			<div class="truncate text-base text-ink-gray-8"><slot /></div>
			<slot name="details" />
			<div v-if="$slots.badge" class="mt-1.5 flex sm:hidden"><slot name="badge" /></div>
		</div>
		<div v-if="$slots.badge" class="hidden sm:col-start-3 sm:flex"><slot name="badge" /></div>
		<div v-if="$slots.actions" class="col-start-3 flex items-center gap-1 sm:col-start-4">
			<slot name="actions" />
		</div>
	</div>
</template>
