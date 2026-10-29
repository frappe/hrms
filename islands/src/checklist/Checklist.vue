<template>
	<section
		class="checklist rounded-lg bg-surface-gray-1 px-3 py-4"
		:data-collapsed="collapsed || null"
	>
		<button
			type="button"
			class="flex w-full items-center gap-2 px-2 text-left focus-visible:rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
			:aria-expanded="!collapsed"
			@click="collapsed = !collapsed"
		>
			<span class="min-w-0 flex-1 text-lg font-medium text-ink-gray-9">{{ title }}</span>
			<span class="whitespace-nowrap text-sm text-ink-gray-5">{{ count }}</span>
			<LucideChevronDown
				class="size-4 shrink-0 text-ink-gray-5 transition-transform duration-200"
				:class="collapsed ? '' : 'rotate-180'"
			/>
		</button>
		<div v-if="progress.total" class="mt-4 px-2">
			<Progress :value="percent" :intervals="progress.total" size="md" />
		</div>
		<div class="fold" :inert="collapsed || null">
			<div>
				<div
					class="items flex flex-col gap-0.5"
					:data-sortable="Boolean(onReorder) || null"
				>
					<ChecklistItem
						v-for="item in ordered"
						:key="item.id"
						:item="item"
						:open="item.id === openId"
						:sortable="Boolean(onReorder)"
						:dragging="item.id === draggingId"
						:can-set-status="Boolean(onStatusChange)"
						:can-assign="Boolean(onAssign)"
						:can-set-due-date="Boolean(onDueDateChange)"
						:can-remove="Boolean(onRemove)"
						:search-users="searchUsers"
						@toggle="toggle(item)"
						@status="(status) => onStatusChange(item.id, status)"
						@assign="(user) => onAssign(item.id, user)"
						@due-date="(date) => onDueDateChange(item.id, date)"
						@skip="() => onSkip(item.id)"
						@unskip="() => onUnskip(item.id)"
						@remove="() => onRemove(item.id)"
						@move="(step) => move(item.id, step)"
						@drag-start="draggingId = item.id"
						@drag-over="() => dragOver(item.id)"
						@drag-end="dragEnd"
					/>
					<label
						v-if="onAdd"
						class="m-0 flex cursor-text items-center gap-3 rounded-md p-2 hover:bg-surface-gray-3 focus-within:bg-surface-base"
					>
						<LucidePlus class="size-4 shrink-0 text-ink-gray-4" />
						<input
							v-model="newLabel"
							type="text"
							class="h-7 min-w-0 flex-1 border-0 bg-transparent p-0 text-base text-ink-gray-8 outline-none ring-0 placeholder:text-ink-gray-5 focus:ring-0"
							:placeholder="addLabel"
							:aria-label="addLabel"
							:readonly="adding"
							@keydown.enter.prevent="add($event.target, true)"
							@keydown.esc="cancelAdd($event.target)"
							@blur="add($event.target, false)"
						/>
					</label>
				</div>
			</div>
		</div>
	</section>
</template>

<script setup>
import { Progress } from "frappe-ui";
import { computed, ref, watch } from "vue";
import LucideChevronDown from "~icons/lucide/chevron-down";
import LucidePlus from "~icons/lucide/plus";

import { __ } from "../translate.js";
import ChecklistItem from "./ChecklistItem.vue";
import { hasBody, isFinished } from "./item.js";

const props = defineProps({
	title: { type: String, default: "" },
	items: { type: Array, default: () => [] },
	addLabel: { type: String, default: () => __("Add item") },
	searchUsers: { type: Function, default: null },
	onAdd: { type: Function, default: null },
	onRemove: { type: Function, default: null },
	onReorder: { type: Function, default: null },
	onSkip: { type: Function, default: null },
	onUnskip: { type: Function, default: null },
	onAssign: { type: Function, default: null },
	onDueDateChange: { type: Function, default: null },
	onStatusChange: { type: Function, default: null },
});

const collapsed = ref(false);
const openId = ref(null);
const openWasFinished = ref(false);
const closedByUser = ref(false);
const order = ref(null);
const draggingId = ref(null);
const newLabel = ref("");
const adding = ref(false);

const ordered = computed(() => {
	if (!order.value) return props.items;
	const byId = new Map(props.items.map((item) => [item.id, item]));
	return order.value.map((id) => byId.get(id)).filter(Boolean);
});

const progress = computed(() => {
	const required = props.items.filter((item) => !item.optional);
	const counted = required.length ? required : props.items;
	return {
		total: counted.length,
		done: counted.filter((item) => item.done).length,
		skipped: counted.filter((item) => !item.done && item.skipped).length,
	};
});

const percent = computed(() => {
	const { total, done, skipped } = progress.value;
	return total ? ((done + skipped) / total) * 100 : 0;
});

const count = computed(() => {
	const { total, done, skipped } = progress.value;
	return skipped
		? __("{0} of {1} done, {2} skipped", [done, total, skipped])
		: __("{0} of {1} done", [done, total]);
});

watch(
	() => props.items,
	() => {
		order.value = null;
		syncOpen();
	},
	{ immediate: true },
);

function syncOpen() {
	const open = props.items.find((item) => item.id === openId.value);
	let next = open;
	if (open && !openWasFinished.value && isFinished(open)) {
		next = nextOpenable(open);
	} else if (!open && !closedByUser.value) {
		next = nextOpenable();
	}
	openId.value = next && hasBody(next, props.onRemove) ? next.id : null;
	openWasFinished.value = Boolean(next && isFinished(next));
}

function nextOpenable(after) {
	const items = props.items;
	const start = after ? items.indexOf(after) + 1 : 0;
	return [...items.slice(start), ...items.slice(0, start)].find(
		(item) => !isFinished(item) && hasBody(item, props.onRemove),
	);
}

function toggle(item) {
	const open = openId.value === item.id ? null : item;
	openId.value = open && hasBody(open, props.onRemove) ? open.id : null;
	openWasFinished.value = Boolean(open && isFinished(open));
	closedByUser.value = !openId.value;
}

function ids() {
	return ordered.value.map((item) => item.id);
}

function reorder(next) {
	const previous = props.items.map((item) => item.id);
	if (next.join() === previous.join()) {
		order.value = null;
		return;
	}
	order.value = next;
	Promise.resolve(props.onReorder?.(next)).catch(() => (order.value = null));
}

function move(id, step) {
	const next = ids();
	const from = next.indexOf(id);
	const to = from + step;
	if (to < 0 || to >= next.length) return;
	next.splice(to, 0, ...next.splice(from, 1));
	reorder(next);
}

function dragOver(id) {
	if (!draggingId.value || draggingId.value === id) return;
	const next = ids();
	const from = next.indexOf(draggingId.value);
	next.splice(next.indexOf(id), 0, ...next.splice(from, 1));
	order.value = next;
}

function dragEnd() {
	draggingId.value = null;
	reorder(ids());
}

function add(input, refocus) {
	const label = newLabel.value.trim();
	if (adding.value || !label) return;
	adding.value = true;
	Promise.resolve(props.onAdd?.(label))
		.then(() => (newLabel.value = ""))
		.catch(() => {})
		.finally(() => {
			adding.value = false;
			if (refocus) input.focus();
		});
}

function cancelAdd(input) {
	newLabel.value = "";
	input.blur();
}
</script>

<style scoped>
.checklist {
	container-type: inline-size;
}
.fold {
	display: grid;
	grid-template-rows: 1fr;
	transition: grid-template-rows 200ms ease-out;
}
.fold > * {
	min-height: 0;
	overflow: hidden;
}
.checklist[data-collapsed] .fold {
	grid-template-rows: 0fr;
}
.items > :first-child {
	margin-top: 1rem;
}
.items[data-sortable] {
	margin-inline-start: -0.75rem;
	padding-inline-start: 0.75rem;
}
@media (prefers-reduced-motion: reduce) {
	.fold {
		transition: none;
	}
}
</style>
