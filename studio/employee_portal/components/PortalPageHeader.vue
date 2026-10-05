<template>
	<PageHeader>
		<div class="flex h-12 w-full min-w-0 items-center gap-2">
			<span
				v-if="icon"
				:class="[icon, 'size-4 shrink-0 text-ink-gray-6']"
				aria-hidden="true"
			/>
			<h1 class="truncate text-base-medium text-ink-gray-9">{{ title }}</h1>
		</div>
	</PageHeader>
</template>

<script setup lang="ts">
import { PageHeader } from "frappe-ui";

defineProps<{ title: string; icon?: string }>();
</script>
