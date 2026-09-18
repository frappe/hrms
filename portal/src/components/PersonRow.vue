<template>
	<component
		:is="to ? 'RouterLink' : 'div'"
		:to="to"
		class="flex min-w-0 items-center gap-2.5"
		:class="to && 'group'"
	>
		<Avatar :label="name" :image="image" :size="size" />
		<div class="min-w-0 leading-tight">
			<div
				class="truncate text-p-base text-ink-gray-9"
				:class="to && 'group-hover:underline'"
			>
				{{ name }}
			</div>
			<div v-if="meta" class="truncate text-base text-ink-gray-5">{{ meta }}</div>
		</div>
		<slot />
	</component>
</template>

<script setup>
import { Avatar } from "frappe-ui";

defineProps({
	name: String,
	image: String,
	meta: String,
	to: [String, Object],
	size: { type: String, default: "lg" },
});
</script>
