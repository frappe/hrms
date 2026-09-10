<template>
	<div class="rounded-6 border border-outline-gray-1 bg-surface-base">
		<div class="flex flex-wrap items-start gap-4 p-4">
			<Avatar :label="name" :image="image" size="3xl" />
			<div class="min-w-0 flex-1">
				<h1 class="truncate text-lg-semibold text-ink-gray-9 sm:text-2xl">
					{{ name }}
				</h1>
				<p class="mt-0.5 truncate text-p-base text-ink-gray-5">{{ meta }}</p>
				<div v-if="badges?.length" class="mt-2 flex flex-wrap gap-1.5">
					<StatusBadge
						v-for="b in badges"
						:key="b.label"
						:status="b.tone"
						:label="b.label"
					/>
				</div>
			</div>
			<div v-if="$slots.actions" class="flex w-full flex-wrap gap-2 sm:w-auto">
				<slot name="actions" />
			</div>
		</div>

		<dl
			v-if="facts?.length"
			class="grid grid-cols-2 border-t border-outline-gray-1 sm:grid-cols-3 lg:grid-cols-5"
		>
			<div
				v-for="fact in facts"
				:key="fact.label"
				class="border-b border-r border-outline-gray-1 px-4 py-2 last:border-r-0 sm:border-b-0"
			>
				<dd class="nums truncate text-base-semibold text-ink-gray-9">
					{{ fact.value || "—" }}
				</dd>
				<dt class="mt-px truncate text-base text-ink-gray-5">
					{{ fact.label }}
				</dt>
			</div>
		</dl>
	</div>
</template>

<script setup>
import { Avatar } from "frappe-ui";
import StatusBadge from "@/components/StatusBadge.vue";

defineProps({
	name: String,
	image: String,
	meta: String,
	badges: Array,
	facts: Array,
});
</script>
