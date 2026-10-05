<template>
	<HoverCard v-if="people.length" side="bottom" align="start">
		<template #trigger>
			<span class="inline-flex items-center gap-2">
				<span class="flex items-center">
					<span
						v-for="(person, index) in shown"
						:key="person.name"
						class="relative flex rounded-full bg-surface-base p-0.5"
						:style="index ? 'margin-left: -0.5rem' : ''"
					>
						<Avatar
							:image="person.image ?? undefined"
							:label="person.name"
							size="sm"
						/>
					</span>
					<span
						v-if="rest > 0"
						class="relative flex rounded-full bg-surface-base p-0.5"
						style="margin-left: -0.5rem"
					>
						<span
							class="flex size-6 items-center justify-center rounded-full bg-surface-gray-3 text-2xs font-medium text-ink-gray-7"
						>
							+{{ rest }}
						</span>
					</span>
				</span>
				<span v-if="label" class="text-base text-ink-gray-7">{{ label }}</span>
			</span>
		</template>
		<div class="max-h-96 w-64 overflow-y-auto p-1">
			<div
				v-for="person in people"
				:key="person.name"
				class="flex items-center gap-2.5 rounded-4 px-2 py-1.5"
			>
				<Avatar :image="person.image ?? undefined" :label="person.name" size="md" />
				<div class="min-w-0">
					<div class="truncate text-base text-ink-gray-8">{{ person.name }}</div>
					<div v-if="person.sub" class="truncate text-sm text-ink-gray-5">
						{{ person.sub }}
					</div>
				</div>
			</div>
		</div>
	</HoverCard>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { Avatar, HoverCard } from "frappe-ui";

type Person = { name: string; image?: string | null; sub?: string };

const props = withDefaults(defineProps<{ people?: Person[]; label?: string }>(), {
	people: () => [],
	label: "",
});

const MAX_FACES = 3;
const shown = computed(() => props.people.slice(0, MAX_FACES));
const rest = computed(() => props.people.length - shown.value.length);
</script>
