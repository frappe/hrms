<script setup>
import { computed } from "vue";
import { Avatar } from "frappe-ui";

const props = defineProps({
	node: { type: Object, required: true },
	open: { type: Boolean, default: false },
	// the way the team opens from the card: "down" under it, or "right" beside it
	direction: { type: String, default: "down" },
});

defineEmits(["toggle"]);

const __ = window.__;
const label = computed(() =>
	props.open
		? __("Hide the team of {0}", [props.node.name])
		: __("Show the team of {0}", [props.node.name]),
);
// Written out whole, so Tailwind's scan finds every icon class
const CHEVRONS = {
	down: { open: "lucide-chevron-up", closed: "lucide-chevron-down" },
	right: { open: "lucide-chevron-left", closed: "lucide-chevron-right" },
};
const chevron = computed(() => CHEVRONS[props.direction][props.open ? "open" : "closed"]);
</script>

<template>
	<button
		type="button"
		class="group flex h-6 items-center gap-1.5 rounded-4 border border-outline-gray-2 bg-surface-base px-1 text-sm text-ink-gray-7 transition-colors hover:bg-surface-gray-2"
		:aria-expanded="open"
		:aria-label="label"
		@click="$emit('toggle')"
	>
		<template v-if="!open">
			<span class="flex -space-x-1.5">
				<span
					v-for="member in node.team"
					:key="member.id"
					class="relative flex rounded-full bg-surface-base p-0.5 transition-colors group-hover:bg-surface-gray-2"
				>
					<Avatar :image="member.image" :label="member.name" size="xs" />
				</span>
			</span>
			<span class="tabular-nums">{{ node.reports }}</span>
		</template>
		<span :class="chevron" class="size-3.5 text-ink-gray-6" aria-hidden="true" />
	</button>
</template>
