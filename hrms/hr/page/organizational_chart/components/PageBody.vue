<script setup lang="ts">
// A centred column with the large heading, under desk's page head.
defineProps<{ heading?: string; subtitle?: string }>();
</script>

<template>
	<div class="h-full overflow-y-auto bg-surface-base text-ink-gray-8">
		<div class="px-4 pb-24 pt-8 sm:px-6">
			<div class="mx-auto w-full max-w-3xl">
				<div v-if="heading" class="mb-4">
					<h1 class="break-words text-lg-semibold text-ink-gray-9">{{ heading }}</h1>
					<p v-if="subtitle" class="mt-1 text-p-base text-ink-gray-5">{{ subtitle }}</p>
				</div>
				<slot />
			</div>
		</div>
	</div>
</template>
