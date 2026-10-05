<template>
	<div class="grid grid-cols-2 overflow-hidden rounded-5 border border-outline-gray-1 sm:flex">
		<div
			v-for="(stat, index) in stats"
			:key="stat.label"
			class="flex min-w-0 flex-1 flex-col border-outline-gray-1 px-4 py-3.5"
			:class="cellClasses(index)"
		>
			<div class="truncate text-sm text-ink-gray-5">{{ stat.label }}</div>
			<div class="mt-1.5 truncate text-2xl-semibold tabular-nums text-ink-gray-9">
				{{ stat.value }}
			</div>
			<div v-if="anyAction" class="mt-auto pt-3">
				<Button
					v-if="stat.action"
					:variant="stat.action.variant ?? 'subtle'"
					:icon-left="stat.action.icon"
					:label="stat.action.label"
					:route="stat.action.route"
					:loading="stat.action.loading"
					@click="stat.action.onClick?.()"
				/>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { Button } from "frappe-ui";

type StatAction = {
	label: string;
	icon?: string;
	variant?: "solid" | "subtle";
	route?: string;
	loading?: boolean;
	onClick?: () => void;
};
type Stat = { label: string; value: string | number; action?: StatAction };

const props = withDefaults(defineProps<{ stats?: Stat[] }>(), { stats: () => [] });

const anyAction = computed(() => props.stats.some((stat) => stat.action));
const spanFirst = computed(() => props.stats.length > 1 && props.stats.length % 2 === 1);

// on phones the cells pair up in two columns; an odd first cell takes the whole row
function cellClasses(index: number) {
	const position = spanFirst.value ? index - 1 : index;
	return [
		index > 0 && "sm:border-l",
		spanFirst.value && index === 0 && "col-span-2 border-b sm:border-b-0",
		position >= 0 && position % 2 === 1 && "border-l sm:border-l",
		position > 1 && "border-t sm:border-t-0",
	];
}
</script>
