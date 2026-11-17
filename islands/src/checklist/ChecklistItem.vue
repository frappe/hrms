<template>
	<div
		class="item relative rounded-5 px-4 py-2"
		:class="{ 'opacity-40': dragging }"
		:data-status="state"
		:data-open="open || null"
		:data-locked="lockReason ? true : null"
		:data-empty="!body || null"
		:draggable="draggable || null"
		@dragstart="dragStart"
		@dragover.prevent="emit('drag-over')"
		@dragend="dragEnd"
		@click="clickRow"
	>
		<button
			v-if="sortable"
			type="button"
			class="grip absolute -left-3 top-2 flex h-7 w-3 cursor-grab items-center justify-center rounded-1 text-ink-gray-4 opacity-0 focus-visible:opacity-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
			:aria-label="__('Move')"
			@pointerdown="draggable = true"
			@pointerup="draggable = false"
			@keydown.up.prevent="emit('move', -1)"
			@keydown.down.prevent="emit('move', 1)"
		>
			<LucideGripVertical class="size-3" />
		</button>
		<div class="row" :data-compact="!showOwner || null">
			<span class="marker flex" data-control>
				<Tooltip v-if="lockReason" :text="lockReason">
					<span
						class="flex rounded-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
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
						class="flex rounded-4 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
						:aria-label="__('Set status')"
						:title="__('Set status')"
					>
						<StatusMark :state="state" />
					</button>
				</Dropdown>
				<StatusMark v-else :state="state" />
			</span>
			<button
				type="button"
				class="toggle flex min-w-0 flex-col gap-0.5 text-left focus-visible:rounded-4 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
				:aria-expanded="open"
			>
				<span class="flex min-w-0 items-center gap-2">
					<span class="label truncate text-base text-ink-gray-8">{{ item.label }}</span>
					<Badge
						v-if="item.skipped && !item.done"
						:label="__('Skipped')"
						theme="gray"
						size="sm"
					/>
					<Badge
						v-else-if="!finished && item.status"
						:label="STATUS_LABELS[item.status]"
						:theme="item.status === 'stuck' ? 'red' : 'gray'"
						size="sm"
					/>
					<Badge
						v-else-if="!finished && item.badge"
						:label="item.badge.label"
						:theme="item.badge.theme"
						size="sm"
					/>
				</span>
				<span v-if="item.value" class="truncate text-p-sm text-ink-gray-5">{{
					item.value
				}}</span>
			</button>
			<div v-if="showOwner" class="owner flex pr-2" data-control>
				<Combobox
					v-if="canAssign"
					trigger="button"
					:model-value="item.assignee?.value ?? null"
					:options="userOptions"
					:filterable="false"
					:loading="searching"
					:placeholder="__('Set assignee')"
					@update:model-value="assign"
					@update:query="search"
					@update:open="(isOpen) => isOpen && search('')"
				>
					<template #trigger>
						<button
							type="button"
							class="flex rounded-full focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
							:title="assigneeTitle"
							:aria-label="assigneeTitle"
						>
							<Avatar
								v-if="item.assignee"
								:label="item.assignee.label"
								:image="item.assignee.image"
								size="md"
							/>
							<span v-else class="unassigned">
								<LucideUserPlus class="size-3" />
							</span>
						</button>
					</template>
					<template #item-prefix="{ item: option }">
						<Avatar :label="option.label" :image="option.image" size="sm" />
					</template>
					<template v-if="item.assignee" #footer="{ clear, close }">
						<Button
							class="w-full !justify-start"
							variant="ghost"
							:label="__('Unassign')"
							@click="clear(), close()"
						/>
					</template>
				</Combobox>
				<span v-else class="flex" :title="assigneeTitle">
					<Avatar
						v-if="item.assignee"
						:label="item.assignee.label"
						:image="item.assignee.image"
						size="md"
					/>
					<span v-else class="unassigned" />
				</span>
			</div>
			<div class="due whitespace-nowrap text-p-sm" data-control>
				<DatePicker
					v-if="canSetDueDate"
					:model-value="item.due_date || ''"
					align="end"
					@update:model-value="setDueDate"
				>
					<template #trigger="{ setOpen, open: pickerOpen }">
						<button
							type="button"
							class="rounded px-1 hover:bg-surface-gray-3 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
							:class="dueClass"
							:title="item.due_date_title || __('Due date')"
							@click="setOpen(!pickerOpen)"
						>
							{{ item.due_date_label || __("Set due date") }}
						</button>
					</template>
					<template v-if="item.due_date" #actions="{ clear }">
						<Button variant="ghost" :label="__('Clear')" @click="clear" />
					</template>
				</DatePicker>
				<span v-else class="px-1" :class="dueClass" :title="item.due_date_title">{{
					item.due_date_label || __("No date")
				}}</span>
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
import { computed, h, ref } from "vue";
import LucideGripVertical from "~icons/lucide/grip-vertical";
import LucideLock from "~icons/lucide/lock";
import LucideUserPlus from "~icons/lucide/user-plus";

import { __ } from "../translate.js";
import { getState, hasBody, isFinished } from "./item.js";
import StatusMark from "./StatusMark.vue";

const statusIcon = (state) => () => h(StatusMark, { state });

const STATUS_LABELS = { in_progress: __("In Progress"), stuck: __("Stuck") };

const props = defineProps({
	item: { type: Object, required: true },
	open: Boolean,
	sortable: Boolean,
	dragging: Boolean,
	canSetStatus: Boolean,
	canAssign: Boolean,
	showOwner: Boolean,
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

const assigneeTitle = computed(() => {
	const assignee = props.item.assignee;
	if (assignee) return assignee.description || assignee.label;
	return props.canAssign ? __("Set assignee") : __("Unassigned");
});

const dueClass = computed(() => {
	if (!props.item.due_date || lockReason.value) return "!text-ink-gray-5";
	if (props.item.overdue && !finished.value) return "!text-ink-red-7";
	return "!text-ink-gray-7";
});

const statusOptions = computed(() => {
	const options = ["in_progress", "stuck"]
		.filter((status) => status !== props.item.status)
		.map((status) => ({
			label: STATUS_LABELS[status],
			icon: statusIcon(status),
			onClick: () => call(props.onStatus, status),
		}));
	if (props.item.status) {
		options.push({
			label: __("Clear status"),
			icon: statusIcon("pending"),
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
		onClick: () => call(action.onClick),
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
	if (event.target.closest("[data-control], .drawer, .grip") || !body.value) return;
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
	display: grid;
	grid-template-columns: subgrid;
	transition:
		padding-block 200ms ease-out,
		background-color 200ms ease-out;
}
.item:hover .grip {
	opacity: 1;
}
.item:not([data-open], [data-empty]) {
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
.row,
.drawer {
	grid-column: 1 / -1;
}
.row {
	display: grid;
	grid-template-columns: subgrid;
	align-items: start;
}
.marker,
.owner,
.due,
.toggle > :first-child {
	display: flex;
	align-items: center;
	min-height: 28px;
}
.toggle > :nth-child(2) {
	margin-top: -4px;
}
.unassigned {
	display: flex;
	align-items: center;
	justify-content: center;
	width: 24px;
	height: 24px;
	flex: none;
	border: 1px dashed var(--outline-gray-4);
	border-radius: 9999px;
	color: var(--ink-gray-5);
}
.marker {
	color: var(--ink-gray-9);
}
.item[data-locked] .marker {
	color: var(--ink-gray-4);
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
