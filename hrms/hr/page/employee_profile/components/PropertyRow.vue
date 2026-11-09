<script setup>
// One label and value row of a private card. With an href, the value is a link.
defineProps({
	label: { type: String, required: true },
	icon: { type: String, default: null },
	value: { type: [String, Number], default: null },
	href: { type: String, default: null },
});
</script>

<template>
	<div class="flex min-h-9 items-start gap-3 py-1.5">
		<div class="flex w-36 shrink-0 items-center gap-2 pt-px text-base text-ink-gray-5 sm:w-40">
			<span :class="icon" class="size-4 shrink-0 text-ink-gray-5" />
			<span class="truncate">{{ label }}</span>
		</div>
		<div class="min-w-0 flex-1 whitespace-pre-line break-words text-base text-ink-gray-8">
			<a
				v-if="href && value"
				:href="href"
				target="_blank"
				rel="noopener noreferrer"
				class="block truncate hover:underline"
			>
				{{ value }}
			</a>
			<template v-else>{{ value || "-" }}</template>
		</div>
	</div>
</template>
