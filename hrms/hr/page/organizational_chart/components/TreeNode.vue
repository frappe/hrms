<script setup>
import { computed, inject } from "vue";
import EmployeeCard from "./EmployeeCard.vue";
import TeamToggle from "./TeamToggle.vue";

const props = defineProps({
	id: { type: String, required: true },
});

const chart = inject("org_chart");
const node = computed(() => chart.nodes[props.id]);
const open = computed(() => chart.expanded.has(props.id));
const team = computed(() => (open.value ? chart.teams[props.id] || [] : []));
const list_view = computed(() => chart.view.value === "list");
const columns_view = computed(() => chart.view.value === "columns");

// The list stacks every team. The tree stacks a team only when no member has reports, so a
// large team does not stretch the chart sideways.
const stacked = computed(
	() => list_view.value || team.value.every((member) => !chart.nodes[member].reports),
);

// the line from the bar down to each card, rounded at both ends of the bar
function connector(index) {
	const last = team.value.length - 1;
	if (!last) return "left-1/2 top-0 h-8 border-l";
	if (index === 0) return "left-1/2 right-0 top-0 h-8 rounded-tl-[12px] border-l border-t";
	if (index === last) {
		return "left-0 right-[calc(50%_-_1px)] top-0 h-8 rounded-tr-[12px] border-r border-t";
	}
	return "inset-x-0 top-0 h-8 border-t";
}

// In a stacked team each member draws its own piece of the line. top-7 is the middle of a 56px
// card, and the curve into the last card starts at top-4. The list's 20px gap fits a team pill.
function line_above(index) {
	const last = index === team.value.length - 1;
	if (index === 0) return last ? "-top-8 h-12" : "-top-8 h-[60px]";
	if (list_view.value) return last ? "-top-5 h-9" : "-top-5 h-12";
	return last ? "-top-2 h-6" : "-top-2 h-9";
}

// Columns: a team sits right of its manager, joined by a spine 32px along (left-8, -left-8).
// Members are 24px apart, room for a team pill.
function spine_above(index) {
	return index === team.value.length - 1 ? "-top-6 h-10" : "-top-6 h-[52px]";
}
</script>

<template>
	<div v-if="columns_view" class="flex items-start">
		<!-- on the card's right edge, 12px in, so a wide pill covers no text -->
		<div class="relative shrink-0">
			<EmployeeCard :node="node" />
			<TeamToggle
				v-if="node.reports"
				:node="node"
				:open="open"
				direction="right"
				class="absolute left-full top-1/2 z-10 -ml-3 -translate-y-1/2"
				@toggle="chart.toggle(id)"
			/>
		</div>

		<div v-if="team.length" class="relative flex flex-col gap-6 pl-16">
			<span
				class="pointer-events-none absolute left-0 top-7 w-8 border-t border-outline-gray-3"
			/>
			<div v-for="(member, index) in team" :key="member" class="relative">
				<span
					v-if="index > 0"
					class="pointer-events-none absolute -left-8 border-l border-outline-gray-3"
					:class="spine_above(index)"
				/>
				<span
					v-if="index < team.length - 1"
					class="pointer-events-none absolute -left-8 bottom-0 top-7 border-l border-outline-gray-3"
				/>
				<span
					v-if="index > 0 && index === team.length - 1"
					class="pointer-events-none absolute -left-8 top-4 h-3 w-8 rounded-bl-[12px] border-b border-l border-outline-gray-3"
				/>
				<span
					v-else
					class="pointer-events-none absolute -left-8 top-7 w-8 border-t border-outline-gray-3"
				/>
				<TreeNode :id="member" />
			</div>
		</div>
	</div>

	<div v-else class="flex flex-col" :class="list_view ? 'items-start' : 'items-center'">
		<div class="relative">
			<EmployeeCard :node="node" />
			<TeamToggle
				v-if="node.reports"
				:node="node"
				:open="open"
				class="absolute left-1/2 top-full z-10 -mt-1.5 -translate-x-1/2"
				@toggle="chart.toggle(id)"
			/>
		</div>

		<div
			v-if="team.length && stacked"
			class="flex flex-col pl-12 pt-8"
			:class="list_view ? 'gap-5' : 'w-64 gap-2'"
		>
			<div v-for="(member, index) in team" :key="member" class="relative">
				<span
					class="pointer-events-none absolute -left-3 border-l border-outline-gray-3"
					:class="line_above(index)"
				/>
				<template v-if="index < team.length - 1">
					<span
						class="pointer-events-none absolute -left-3 bottom-0 top-7 border-l border-outline-gray-3"
					/>
					<span
						class="pointer-events-none absolute -left-3 top-7 w-3 border-t border-outline-gray-3"
					/>
				</template>
				<span
					v-else
					class="pointer-events-none absolute -left-3 top-4 h-3 w-3 rounded-bl-[12px] border-b border-l border-outline-gray-3"
				/>
				<TreeNode :id="member" />
			</div>
		</div>

		<div v-else-if="team.length" class="relative flex items-start pt-8">
			<span
				class="pointer-events-none absolute left-1/2 top-0 h-8 border-l border-outline-gray-3"
			/>
			<div v-for="(member, index) in team" :key="member" class="relative px-2.5 pt-8">
				<span
					class="pointer-events-none absolute border-outline-gray-3"
					:class="connector(index)"
				/>
				<span
					v-if="index > 0 && index < team.length - 1"
					class="pointer-events-none absolute left-1/2 top-0 h-8 border-l border-outline-gray-3"
				/>
				<TreeNode :id="member" />
			</div>
		</div>
	</div>
</template>
