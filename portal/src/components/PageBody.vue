<template>
	<div class="mx-auto flex w-full max-w-[1440px] flex-col gap-3.5 p-3 sm:p-4 lg:p-5">
		<div v-if="loading" class="flex items-center gap-2 py-6 text-base text-ink-gray-5">
			<LoadingIndicator class="h-4 w-4" />
			Loading
		</div>
		<template v-else>
			<slot />
		</template>
	</div>
</template>

<script setup>
import { LoadingIndicator } from "frappe-ui";

defineProps({ loading: Boolean });
</script>
