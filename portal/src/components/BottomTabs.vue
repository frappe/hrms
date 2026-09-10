<template>
	<nav
		class="grid shrink-0 grid-cols-5 border-t border-outline-gray-1 bg-surface-base pb-safe-bottom"
		aria-label="Sections"
	>
		<template v-for="tab in TABS" :key="tab.label">
			<!--
				Explicit elements rather than <component :is>: the string "button"
				resolves to the globally registered frappe-ui Button component.
			-->
			<RouterLink v-if="tab.to" :to="tab.to" :class="[tabClass, toneClass(tab)]">
				<span :class="[tab.icon, 'h-[18px] w-[18px]']" aria-hidden="true" />
				<span class="text-[10px]" :class="isActive(tab) && 'font-semibold'">
					{{ tab.label }}
				</span>
			</RouterLink>
			<button
				v-else
				type="button"
				:class="[tabClass, toneClass(tab)]"
				@click="$emit(tab.action)"
			>
				<span :class="[tab.icon, 'h-[18px] w-[18px]']" aria-hidden="true" />
				<span class="text-[10px]">{{ tab.label }}</span>
			</button>
		</template>
	</nav>
</template>

<script setup>
import { useRoute } from "vue-router";
import { TABS } from "@/nav";

defineEmits(["more"]);

const route = useRoute();
const tabClass = "flex flex-col items-center gap-0.5 py-2 transition-colors";

function isActive(tab) {
	if (!tab.to) return false;
	return route.path === tab.to || route.path.startsWith(tab.to + "/");
}

function toneClass(tab) {
	return isActive(tab) ? "text-ink-gray-9" : "text-ink-gray-4";
}
</script>
