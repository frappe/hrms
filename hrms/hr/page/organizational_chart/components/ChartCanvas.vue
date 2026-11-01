<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import { Button, Divider, Tooltip } from "frappe-ui";
import { export_image } from "../export_image.js";

const props = defineProps({
	// the card the popover belongs to
	selected: { type: String, default: null },
});

const emit = defineEmits(["deselect"]);

const __ = window.__;

// past the scale the whole chart fits at, zooming out only makes the cards harder to read
const MAX_SCALE = 1.5;
const ZOOM_STEP = 1.2;
const GRID_SIZE = 20;
// gap between a card and its popover, and the popover's minimum distance from the canvas edge
const POPOVER_GAP = 12;
const EDGE_GAP = 16;
// how far a card's team pill hangs below the card
const TEAM_PILL_DROP = 18;
// a pointer that moves less than this between down and up is a click, not a drag
const CLICK_DISTANCE = 4;

const canvas = ref(null);
const content = ref(null);
const popover = ref(null);
const panel = ref(null);
const toolbar = ref(null);
const popover_style = ref({ visibility: "hidden" });
const view = reactive({ x: 0, y: 0, scale: 1 });
const dragging = ref(false);

const canvas_style = computed(() => ({
	backgroundImage: "radial-gradient(circle, var(--outline-gray-2) 1px, transparent 1.2px)",
	backgroundSize: `${GRID_SIZE * view.scale}px ${GRID_SIZE * view.scale}px`,
	backgroundPosition: `${view.x}px ${view.y}px`,
}));
const content_style = computed(() => ({
	transform: `translate(${view.x}px, ${view.y}px) scale(${view.scale})`,
	transformOrigin: "0 0",
}));

// the scale the whole chart fits the canvas at, and never above full size
function fit_scale() {
	const rect = canvas.value.getBoundingClientRect();
	const { offsetWidth: width, offsetHeight: height } = content.value;
	return Math.min(1, rect.width / width, rect.height / height);
}

// zooms around `point` (default: the middle), so it stays under the pointer
function zoom_to(scale, point) {
	const next = Math.min(MAX_SCALE, Math.max(fit_scale(), scale));
	const rect = canvas.value.getBoundingClientRect();
	const { x, y } = point || { x: rect.width / 2, y: rect.height / 2 };
	view.x = x - ((x - view.x) * next) / view.scale;
	view.y = y - ((y - view.y) * next) / view.scale;
	view.scale = next;
}

function fit() {
	const rect = canvas.value.getBoundingClientRect();
	const { offsetWidth: width, offsetHeight: height } = content.value;
	view.scale = fit_scale();
	view.x = (rect.width - width * view.scale) / 2;
	view.y = (rect.height - height * view.scale) / 2;
}

// the top of the chart, centred, at full size, below the panel
function show_top() {
	const rect = canvas.value.getBoundingClientRect();
	const panel_bottom = panel.value ? panel.value.offsetTop + panel.value.offsetHeight : 0;
	const content_padding = parseFloat(getComputedStyle(content.value).paddingTop);

	view.scale = 1;
	view.x = (rect.width - content.value.offsetWidth) / 2;
	view.y = Math.max(0, panel_bottom + EDGE_GAP - content_padding);
}

// moves the view so `element` is in the middle of the canvas
function center(element) {
	const rect = canvas.value.getBoundingClientRect();
	const box = element.getBoundingClientRect();
	view.x += rect.left + rect.width / 2 - (box.left + box.width / 2);
	view.y += rect.top + rect.height / 2 - (box.top + box.height / 2);
}

// runs `change`, then keeps `element` where it was on screen
async function keep_in_place(element, change) {
	const before = element?.getBoundingClientRect();
	await change();
	await nextTick();
	if (!before || !element.isConnected) return;

	const after = element.getBoundingClientRect();
	view.x += before.left - after.left;
	view.y += before.top - after.top;
}

// Moves the view, and zooms out as far as it must, so every one of `elements` is in sight
// between the panel and the toolbar. Nothing moves when they already are.
function reveal(elements) {
	const boxes = elements.filter(Boolean).map((element) => element.getBoundingClientRect());
	if (!boxes.length) return;

	const rect = canvas.value.getBoundingClientRect();
	const area = {
		left: EDGE_GAP,
		right: rect.width - EDGE_GAP,
		top: (panel.value ? panel.value.offsetTop + panel.value.offsetHeight : 0) + EDGE_GAP,
		bottom: (toolbar.value ? toolbar.value.offsetTop : rect.height) - EDGE_GAP,
	};
	let left = Math.min(...boxes.map((box) => box.left)) - rect.left;
	let top = Math.min(...boxes.map((box) => box.top)) - rect.top;
	// the last row of cards has its team pills hanging below
	let right = Math.max(...boxes.map((box) => box.right)) - rect.left;
	let bottom = Math.max(...boxes.map((box) => box.bottom)) - rect.top + TEAM_PILL_DROP;
	if (left >= area.left && right <= area.right && top >= area.top && bottom <= area.bottom)
		return;

	const room = Math.min(
		(area.right - area.left) / (right - left),
		(area.bottom - area.top) / (bottom - top),
	);
	if (room < 1) {
		const before = view.scale;
		zoom_to(view.scale * room, { x: left, y: top });
		right = left + ((right - left) * view.scale) / before;
		bottom = top + ((bottom - top) * view.scale) / before;
	}

	// centred across the free area, and only as far down or up as it takes
	view.x += Math.max(area.left - left, (area.left + area.right - left - right) / 2);
	if (top < area.top) view.y += area.top - top;
	else if (bottom > area.bottom) view.y += Math.max(area.bottom - bottom, area.top - top);
}

const find_card = (id) => content.value?.querySelector(`[data-node="${CSS.escape(id)}"]`);

// beside the selected card: right if it fits, else left, else below
function place_popover() {
	if (!props.selected || !popover.value) return;

	// the card is hidden inside a closed team
	const card = find_card(props.selected);
	if (!card) return emit("deselect");

	const rect = canvas.value.getBoundingClientRect();
	const box = card.getBoundingClientRect();
	const { offsetWidth: width, offsetHeight: height } = popover.value;

	const right_side = box.right - rect.left + POPOVER_GAP;
	const left_side = box.left - rect.left - POPOVER_GAP - width;
	let left = right_side;
	let top = box.top - rect.top;
	if (right_side + width > rect.width - EDGE_GAP) {
		if (left_side >= EDGE_GAP) {
			left = left_side;
		} else {
			// no room on either side (phones): below the card and its team pill
			left = box.left - rect.left;
			top = box.bottom - rect.top + TEAM_PILL_DROP + POPOVER_GAP;
		}
	}

	left = Math.max(EDGE_GAP, Math.min(left, rect.width - width - EDGE_GAP));
	top = Math.max(EDGE_GAP, Math.min(top, rect.height - height - EDGE_GAP));
	popover_style.value = { left: `${left}px`, top: `${top}px` };
}

watch(
	() => [props.selected, view.x, view.y, view.scale],
	([selected], [before] = []) => {
		// a new popover stays hidden until it is measured and placed
		if (selected !== before) popover_style.value = { visibility: "hidden" };
		nextTick(place_popover);
	},
);

// opening or closing a team elsewhere moves the card
const resize_observer = new ResizeObserver(() => place_popover());
onMounted(() => resize_observer.observe(content.value));
onBeforeUnmount(() => resize_observer.disconnect());

let drag = null;
// fingers on the canvas by pointer id. Two of them pinch to zoom.
const pointers = new Map();
let pinch = null;

const finger_gap = ([a, b]) => Math.hypot(a.x - b.x, a.y - b.y);

function start_drag(event) {
	if (event.button !== 0 || event.target.closest("button, input, [data-panel]")) return;
	pointers.set(event.pointerId, { x: event.clientX, y: event.clientY });
	canvas.value.setPointerCapture(event.pointerId);

	if (pointers.size === 2) {
		pinch = { gap: finger_gap([...pointers.values()]), scale: view.scale };
		drag = null;
		return;
	}
	drag = {
		x: event.clientX - view.x,
		y: event.clientY - view.y,
		from_x: event.clientX,
		from_y: event.clientY,
	};
	dragging.value = true;
}

function move_drag(event) {
	if (!pointers.has(event.pointerId)) return;
	pointers.set(event.pointerId, { x: event.clientX, y: event.clientY });

	if (pinch && pointers.size === 2) {
		const fingers = [...pointers.values()];
		const rect = canvas.value.getBoundingClientRect();
		zoom_to((pinch.scale * finger_gap(fingers)) / pinch.gap, {
			x: (fingers[0].x + fingers[1].x) / 2 - rect.left,
			y: (fingers[0].y + fingers[1].y) / 2 - rect.top,
		});
		return;
	}
	if (!drag) return;
	view.x = event.clientX - drag.x;
	view.y = event.clientY - drag.y;
}

function stop_drag(event) {
	pointers.delete(event.pointerId);
	// a click on the canvas itself, between the cards, closes the popover
	if (
		drag &&
		!pinch &&
		Math.hypot(event.clientX - drag.from_x, event.clientY - drag.from_y) < CLICK_DISTANCE
	) {
		emit("deselect");
	}
	if (!pointers.size) pinch = null;
	drag = null;
	dragging.value = false;
}

function on_wheel(event) {
	if (event.target.closest("[data-panel]")) return;
	event.preventDefault();

	// a pinch on a trackpad arrives as a wheel event with ctrlKey set
	if (event.ctrlKey || event.metaKey) {
		const rect = canvas.value.getBoundingClientRect();
		zoom_to(view.scale * Math.exp(-event.deltaY / 100), {
			x: event.clientX - rect.left,
			y: event.clientY - rect.top,
		});
		return;
	}
	view.x -= event.deltaX;
	view.y -= event.deltaY;
}

function on_keydown(event) {
	if (event.key === "Escape") return emit("deselect");
	if (event.target.closest("input")) return;

	if (event.key === "+" || event.key === "=") zoom_to(view.scale * ZOOM_STEP);
	else if (event.key === "-") zoom_to(view.scale / ZOOM_STEP);
	else if (event.key === "0") fit();
	else return;
	event.preventDefault();
}

// the chart at full size whatever the zoom, with the open teams
const save_image = (file_name) => export_image(content.value, file_name);

defineExpose({ fit, show_top, center, keep_in_place, reveal, find_card, save_image });
</script>

<template>
	<div
		ref="canvas"
		tabindex="0"
		role="application"
		:aria-label="__('Org chart. Drag to move, plus and minus to zoom, 0 to fit.')"
		class="relative h-full w-full touch-none select-none overflow-hidden bg-surface-base outline-none"
		:class="dragging ? 'cursor-grabbing' : 'cursor-grab'"
		:style="canvas_style"
		@pointerdown="start_drag"
		@pointermove="move_drag"
		@pointerup="stop_drag"
		@pointercancel="stop_drag"
		@wheel="on_wheel"
		@keydown="on_keydown"
	>
		<div
			ref="content"
			class="absolute left-0 top-0 inline-flex flex-col items-center p-10"
			:style="content_style"
		>
			<slot />
		</div>

		<div
			v-if="selected && $slots.popover"
			ref="popover"
			data-panel
			class="absolute z-10 cursor-auto"
			:style="popover_style"
		>
			<slot name="popover" />
		</div>

		<div
			v-if="$slots.panel"
			ref="panel"
			data-panel
			class="absolute left-4 right-4 top-4 rounded-4 bg-surface-base sm:right-auto"
		>
			<slot name="panel" />
		</div>

		<div
			ref="toolbar"
			data-panel
			class="absolute bottom-4 left-4 flex items-center gap-0.5 rounded-5 border border-outline-gray-2 bg-surface-base p-1"
		>
			<Tooltip :text="__('Zoom out')">
				<Button
					variant="ghost"
					icon="lucide-minus"
					:aria-label="__('Zoom out')"
					@click="zoom_to(view.scale / ZOOM_STEP)"
				/>
			</Tooltip>
			<Tooltip :text="__('Reset to 100%')">
				<Button
					variant="ghost"
					class="min-w-12 tabular-nums"
					:label="`${Math.round(view.scale * 100)}%`"
					@click="zoom_to(1)"
				/>
			</Tooltip>
			<Tooltip :text="__('Zoom in')">
				<Button
					variant="ghost"
					icon="lucide-plus"
					:aria-label="__('Zoom in')"
					@click="zoom_to(view.scale * ZOOM_STEP)"
				/>
			</Tooltip>
			<Divider orientation="vertical" class="mx-1 !h-4" />
			<Tooltip :text="__('Fit to screen')">
				<Button
					variant="ghost"
					icon="lucide-maximize"
					:aria-label="__('Fit to screen')"
					@click="fit"
				/>
			</Tooltip>
			<slot name="actions" />
		</div>
	</div>
</template>
