<template>
	<section
		class="flex flex-col rounded-6 border border-outline-gray-1 bg-surface-base"
		:class="padded ? 'gap-3 p-3.5' : ''"
	>
		<header
			v-if="title || $slots.action"
			class="flex items-center justify-between gap-2"
			:class="!padded && 'px-3.5 pb-2.5 pt-3'"
		>
			<h2 class="text-base-semibold text-ink-gray-9">{{ title }}</h2>
			<div class="shrink-0">
				<slot name="action">
					<!-- one affordance per card: Edit, Add, or the words HR-owned -->
					<Button
						v-if="action"
						class="-mr-2"
						variant="ghost"
						:label="action"
						@click="$emit('action')"
					/>
					<span v-else-if="readonlyLabel" class="text-base text-ink-gray-5">
						{{ readonlyLabel }}
					</span>
				</slot>
			</div>
		</header>
		<slot />
	</section>
</template>

<script setup>
import { Button } from "frappe-ui";
defineProps({
	title: String,
	action: String,
	readonlyLabel: String,
	padded: { type: Boolean, default: true },
});
defineEmits(["action"]);
</script>
