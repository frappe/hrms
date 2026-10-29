<template>
	<div
		class="item relative rounded-md p-2"
		:class="{ 'opacity-40': dragging }"
		:data-status="state"
		:data-open="open || null"
		:data-locked="lockReason ? true : null"
		:data-empty="!body || null"
		:draggable="draggable || null"
		@dragstart="dragStart"
		@dragover.prevent="emit('drag-over')"
		@dragend="dragEnd"
	>
		<button
			v-if="sortable"
			type="button"
			class="grip absolute -left-3 top-2 flex h-7 w-3 cursor-grab items-center justify-center rounded-sm text-ink-gray-4 opacity-0 focus-visible:opacity-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
			:aria-label="__('Move')"
			@pointerdown="draggable = true"
			@pointerup="draggable = false"
			@keydown.up.prevent="emit('move', -1)"
			@keydown.down.prevent="emit('move', 1)"
		>
			<LucideGripVertical class="size-3" />
		</button>
		<div class="row" @click="clickRow">
			<span class="marker flex text-ink-gray-4" data-control>
				<Tooltip v-if="lockReason" :text="lockReason">
					<span
						class="flex rounded-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
						tabindex="0"
						role="img"
						:aria-label="lockReason"
					>
						<LucideLock class="size-4" />
					</span>
				</Tooltip>
				<Dropdown v-else-if="canSetStatus && !finished" :options="statusOptions">
					<button
						type="button"
						class="flex rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
						:aria-label="__('Set status')"
						:title="__('Set status')"
					>
						<component :is="MARKERS[state]" class="size-4" />
					</button>
				</Dropdown>
				<component :is="MARKERS[state]" v-else class="size-4" />
			</span>
			<button
				type="button"
				class="toggle flex min-w-0 flex-col gap-0.5 text-left focus-visible:rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
				:aria-expanded="open"
			>
				<span class="flex min-w-0 items-center gap-2">
					<span class="label truncate text-base text-ink-gray-8">{{ item.label }}</span>
					<Badge v-if="item.optional" :label="__('Optional')" size="sm" />
				</span>
				<span v-if="item.value" class="truncate text-p-sm text-ink-gray-5">{{
					item.value
				}}</span>
			</button>
			<div class="status">
				<span v-if="item.skipped && !item.done" class="text-p-sm text-ink-gray-4">
					{{ __("Skipped") }}
				</span>
				<Badge
					v-else-if="!finished && item.status"
					:label="STATUS_LABELS[item.status]"
					:theme="item.status === 'stuck' ? 'red' : 'gray'"
					size="sm"
				/>
			</div>
			<div class="owner flex min-w-0 justify-center text-ink-gray-4" data-control>
				<Combobox
					v-if="canAssign"
					class="min-w-0 max-w-full"
					trigger="button"
					variant="ghost"
					:model-value="item.assignee?.value ?? null"
					:options="userOptions"
					:filterable="false"
					:loading="searching"
					:placeholder="__('Select assignee')"
					@update:model-value="assign"
					@update:query="search"
					@update:open="(isOpen) => isOpen && search('')"
				>
					<template #prefix="{ selectedOption }">
						<Avatar
							v-if="selectedOption"
							:label="selectedOption.label"
							:image="selectedOption.image"
							size="sm"
						/>
					</template>
					<template #item-prefix="{ item: option }">
						<Avatar :label="option.label" :image="option.image" size="sm" />
					</template>
				</Combobox>
				<Avatar
					v-else-if="item.assignee"
					:label="item.assignee.label"
					:image="item.assignee.image"
					size="sm"
				/>
			</div>
			<div
				class="due justify-self-end whitespace-nowrap text-p-sm"
				:class="item.overdue && !finished ? 'text-ink-red-7' : 'text-ink-gray-6'"
				data-control
			>
				<DatePicker
					v-if="canSetDueDate"
					:model-value="item.due_date || ''"
					align="end"
					@update:model-value="setDueDate"
				>
					<template #trigger="{ setOpen, open: pickerOpen }">
						<Button
							variant="ghost"
							:class="dueClass"
							:label="item.due_date_label || __('Add due date')"
							:tooltip="__('Due date')"
							@click="setOpen(!pickerOpen)"
						>
							<template #prefix><LucideCalendar class="size-4" /></template>
						</Button>
					</template>
				</DatePicker>
				<template v-else>{{ item.due_date_label }}</template>
			</div>
		</div>
		<div class="drawer" :inert="!open || null">
			<div>
				<div class="content flex flex-col gap-3 pb-1 pt-2">
					<p v-if="item.description" class="text-p-sm text-ink-gray-6">
						{{ item.description }}
					</p>
					<div v-if="buttons.length" class="flex flex-wrap items-center gap-2">
						<Button
							v-for="button in buttons"
							:key="button.label"
							:label="button.label"
							:variant="button.variant"
							:disabled="button.disabled"
							@click="button.onClick"
						/>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { Avatar, Badge, Button, Combobox, DatePicker, Dropdown, Tooltip } from "frappe-ui";
import { computed, ref } from "vue";
import LucideCalendar from "~icons/lucide/calendar";
import LucideCircle from "~icons/lucide/circle";
import LucideCircleAlert from "~icons/lucide/circle-alert";
import LucideCircleCheck from "~icons/lucide/circle-check";
import LucideCircleDashed from "~icons/lucide/circle-dashed";
import LucideCircleDotDashed from "~icons/lucide/circle-dot-dashed";
import LucideGripVertical from "~icons/lucide/grip-vertical";
import LucideLock from "~icons/lucide/lock";

import { __ } from "../translate.js";
import { getState, hasBody, isFinished } from "./item.js";

const MARKERS = {
	pending: LucideCircle,
	in_progress: LucideCircleDotDashed,
	stuck: LucideCircleAlert,
	done: LucideCircleCheck,
	skipped: LucideCircleDashed,
};

const STATUS_LABELS = { in_progress: __("In Progress"), stuck: __("Stuck") };

const props = defineProps({
	item: { type: Object, required: true },
	open: Boolean,
	sortable: Boolean,
	dragging: Boolean,
	canSetStatus: Boolean,
	canAssign: Boolean,
	canSetDueDate: Boolean,
	canRemove: Boolean,
	searchUsers: { type: Function, default: null },
	onStatus: { type: Function, default: null },
	onAssign: { type: Function, default: null },
	onDueDate: { type: Function, default: null },
	onSkip: { type: Function, default: null },
	onUnskip: { type: Function, default: null },
	onRemove: { type: Function, default: null },
});

const emit = defineEmits(["toggle", "move", "drag-start", "drag-over", "drag-end"]);

const draggable = ref(false);
const searching = ref(false);
const searchResults = ref([]);

const state = computed(() => getState(props.item));
const finished = computed(() => isFinished(props.item));
const lockReason = computed(() => (finished.value ? null : props.item.locked));
const body = computed(() => hasBody(props.item, props.canRemove));

const dueClass = computed(() => {
	if (props.item.overdue && !finished.value) return "!text-ink-red-7";
	return props.item.due_date ? "!text-ink-gray-6" : "!text-ink-gray-5";
});

const statusOptions = computed(() => {
	const options = ["in_progress", "stuck"]
		.filter((status) => status !== props.item.status)
		.map((status) => ({
			label: STATUS_LABELS[status],
			icon: MARKERS[status],
			onClick: () => call(props.onStatus, status),
		}));
	if (props.item.status) {
		options.push({
			label: __("Clear status"),
			icon: LucideCircle,
			onClick: () => call(props.onStatus, null),
		});
	}
	return options;
});

const userOptions = computed(() => {
	const assignee = props.item.assignee;
	const results = searchResults.value.filter((option) => option.value !== assignee?.value);
	return assignee ? [assignee, ...results] : results;
});

const buttons = computed(() => {
	const item = props.item;
	const remove =
		item.removable && props.canRemove
			? [subtle(__("Remove"), () => call(props.onRemove))]
			: [];
	if (item.skipped && !item.done) {
		return item.skippable
			? [subtle(__("Undo skip"), () => call(props.onUnskip)), ...remove]
			: remove;
	}
	const actions = (item.actions || []).map((action, index) => ({
		label: action.label,
		variant: action.variant || (index ? "subtle" : "solid"),
		disabled: Boolean(lockReason.value) || Boolean(action.disabled),
		onClick: () => action.onClick?.(),
	}));
	if (item.skippable && !item.done) actions.push(subtle(__("Skip"), () => call(props.onSkip)));
	return [...actions, ...remove];
});

function subtle(label, onClick) {
	return { label, variant: "subtle", onClick };
}

function call(handler, ...args) {
	return Promise.resolve(handler?.(...args)).catch(() => {});
}

function clickRow(event) {
	if (event.target.closest("[data-control]") || !body.value) return;
	emit("toggle");
}

function assign(user) {
	if ((user || null) === (props.item.assignee?.value ?? null)) return;
	call(props.onAssign, user || null);
}

function setDueDate(date) {
	if ((date || null) === (props.item.due_date || null)) return;
	call(props.onDueDate, date || null);
}

let lastQuery = null;
function search(query) {
	if (!props.searchUsers || query === lastQuery) return;
	lastQuery = query;
	searching.value = true;
	Promise.resolve(props.searchUsers(query))
		.then((options) => {
			if (query === lastQuery) searchResults.value = options || [];
		})
		.finally(() => {
			if (query === lastQuery) searching.value = false;
		});
}

function dragStart(event) {
	if (!draggable.value) return event.preventDefault();
	event.dataTransfer.effectAllowed = "move";
	emit("drag-start");
}

function dragEnd() {
	draggable.value = false;
	emit("drag-end");
}
</script>

<style scoped>
.item {
	transition:
		padding-block 200ms ease-out,
		background-color 200ms ease-out;
}
.item:hover .grip {
	opacity: 1;
}
.item:not([data-open], [data-empty]) .row {
	cursor: pointer;
}
.item:not([data-open], [data-empty]):hover {
	background-color: var(--surface-gray-3);
}
.item[data-open] {
	padding-block: 0.75rem;
	background-color: var(--surface-base);
}
.item[data-empty] .toggle {
	cursor: default;
}
.row {
	display: grid;
	grid-template-columns: auto minmax(0, 1fr) 88px 164px 132px;
	grid-template-areas: "marker text status owner due";
	align-items: center;
	column-gap: 0.75rem;
	min-height: 28px;
}
.marker {
	grid-area: marker;
}
.toggle {
	grid-area: text;
}
.status {
	grid-area: status;
}
.owner {
	grid-area: owner;
}
.due {
	grid-area: due;
}
.item[data-open][data-status="pending"] .marker {
	color: var(--ink-gray-8);
}
.item[data-status="done"] .marker {
	color: var(--ink-green-7);
}
.item[data-status="stuck"] .marker {
	color: var(--ink-red-7);
}
.item:is([data-status="done"], [data-locked]) .label {
	color: var(--ink-gray-5);
}
.item[data-status="skipped"] .label {
	color: var(--ink-gray-4);
}
.item[data-open] .label {
	font-weight: 500;
	color: var(--ink-gray-9);
}
.drawer {
	display: grid;
	grid-template-rows: 0fr;
	transition: grid-template-rows 200ms ease-out;
}
.drawer > * {
	min-height: 0;
	overflow: hidden;
}
.item[data-open] .drawer {
	grid-template-rows: 1fr;
}
.content {
	padding-inline-start: calc(16px + 0.75rem);
}
@container (max-width: 560px) {
	.row {
		grid-template-columns: auto auto auto minmax(56px, 1fr) auto;
		column-gap: 0.5rem;
	}
	.owner {
		justify-content: end;
	}
	.content {
		padding-inline-start: calc(16px + 0.5rem);
	}
}
@media (prefers-reduced-motion: reduce) {
	.item,
	.drawer {
		transition: none;
	}
}
</style>
