<script setup>
import { ref, watch } from "vue";
import { Button } from "frappe-ui";

// One label and value row of a private card. With an href, the value is a link. With reveal, the
// value is shown masked and an eye button fetches the whole of it, such as an account number.
const props = defineProps({
	label: { type: String, required: true },
	icon: { type: String, default: null },
	value: { type: [String, Number], default: null },
	href: { type: String, default: null },
	// () => Promise<string>, the whole value
	reveal: { type: Function, default: null },
});

const __ = window.__;
const whole = ref(null);
const loading = ref(false);

// a saved change shows masked again
watch(
	() => props.value,
	() => (whole.value = null),
);

async function toggle() {
	if (whole.value) {
		whole.value = null;
		return;
	}
	loading.value = true;
	try {
		whole.value = await props.reveal();
	} catch {
		// the server's message is already on screen
	} finally {
		loading.value = false;
	}
}
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
			<template v-else>{{ whole || value || "-" }}</template>
		</div>
		<Button
			v-if="reveal && value"
			class="-my-1 shrink-0"
			variant="ghost"
			:icon="whole ? 'lucide-eye-off' : 'lucide-eye'"
			:loading="loading"
			:tooltip="whole ? __('Hide') : __('Show')"
			:aria-label="whole ? __('Hide {0}', [label]) : __('Show {0}', [label])"
			@click="toggle"
		/>
	</div>
</template>
