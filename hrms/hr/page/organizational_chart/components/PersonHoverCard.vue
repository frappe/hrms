<script setup>
import { computed } from "vue";
import { Avatar, HoverCard } from "frappe-ui";
import { leave_label } from "../utils.js";

const props = defineProps({
	person: { type: Object, required: true },
});

// only a full day away gets a line
const away = computed(() => (props.person.leave?.half_day ? "" : leave_label(props.person.leave)));
</script>

<template>
	<HoverCard side="bottom" align="start">
		<template #trigger>
			<slot />
		</template>

		<div class="w-72 p-4">
			<div class="flex items-center gap-3">
				<Avatar :image="person.image" :label="person.name" size="2xl" />
				<div class="min-w-0">
					<div class="truncate text-base-semibold text-ink-gray-9">
						{{ person.name }}
					</div>
					<div v-if="person.designation" class="truncate text-sm text-ink-gray-5">
						{{ person.designation }}
					</div>
				</div>
			</div>
			<div class="mt-3 space-y-1.5 text-sm text-ink-gray-7">
				<div v-if="person.department" class="flex items-center gap-2">
					<span class="lucide-building-2 size-3.5 text-ink-gray-5" aria-hidden="true" />
					{{ person.department }}
				</div>
				<div v-if="person.branch" class="flex items-center gap-2">
					<span class="lucide-map-pin size-3.5 text-ink-gray-5" aria-hidden="true" />
					{{ person.branch }}
				</div>
				<div v-if="person.email" class="flex items-center gap-2">
					<span class="lucide-mail size-3.5 text-ink-gray-5" aria-hidden="true" />
					<span class="truncate">{{ person.email }}</span>
				</div>
				<div v-if="away" class="flex items-center gap-2 text-ink-blue-7">
					<span class="lucide-tree-palm size-3.5" aria-hidden="true" />
					{{ away }}
				</div>
			</div>
		</div>
	</HoverCard>
</template>
