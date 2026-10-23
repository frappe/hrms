<script setup lang="ts">
// The company as a map you move around. Rooted at the top, opened along the path to you,
// so the first thing you see is where you sit.
//
// Drag or scroll to pan, ctrl/cmd-scroll to zoom at the cursor, + / - / 0 on the keyboard.
// The face-and-count pill opens a team and keeps the node you clicked under your cursor.
// Search flies to anyone. Clicking a person emits `select`; the page opens the sheet.
import { computed, nextTick, onBeforeUnmount, onMounted, provide, ref, watch } from "vue";
import { Button, Combobox, Divider, TabButtons, Tooltip } from "frappe-ui";
import OrgNode from "./OrgNode";
import OrgPersonCard from "./OrgPersonCard.vue";
import { byId, chainOf, deptOf, meId, reportsOf, rootIds, staff } from "../lib/people";

declare const __: (text: string, args?: unknown[]) => string;

// `focus` opens the chart on someone; `person` also selects them (?focus= and ?person= on the page).
const props = defineProps<{ focus?: string; person?: string }>();
const known = (id?: string) => (id && byId.value[id] ? id : "");
const focus = computed(() => known(props.focus) || known(props.person));
// Each visit reloads `staff` behind the chart, so the trees and the people in them follow it.
const ROOTS = rootIds;
const ROOT = computed(() => ROOTS.value[0] || "");
// Someone in a reports_to loop has no top, so no tree to sit in.
const PEOPLE = computed(() =>
	staff.value.filter((p) => !byId.value[chainOf(p.id).at(-1) ?? p.id]?.manager),
);
const you = computed(() => meId.value);
// Administrator and anyone without an employee record open on the top of the chart.
const home = you.value || ROOT.value;
const start = focus.value || home;

const pathTo = (id: string) => [...chainOf(id), id];
const expanded = ref(new Set<string>(pathTo(start)));
const pickedId = ref<string | null>(known(props.person) || null);
const selected = computed(() => pickedId.value || "");
const emit = (e: "select" | "clear", id?: string) =>
	e === "clear" ? (pickedId.value = null) : (pickedId.value = id ?? null);

// ---- orientation: top to bottom, or left to right; remembered per browser ----------------
type Orientation = "vertical" | "horizontal";
const ORIENTATION_KEY = "org-chart-orientation";
function savedOrientation(): Orientation {
	try {
		return localStorage.getItem(ORIENTATION_KEY) === "horizontal" ? "horizontal" : "vertical";
	} catch {
		return "vertical";
	}
}
const orientation = ref<Orientation>(savedOrientation());
const orientations = [
	{ label: __("Top to bottom"), value: "vertical", icon: "lucide-move-down" },
	{ label: __("Left to right"), value: "horizontal", icon: "lucide-move-right" },
];

// ---- the view: one transform, owned here -------------------------------------------
const vp = ref<HTMLElement>();
const stage = ref<HTMLElement>();
const s = ref(1);
const tx = ref(0);
const ty = ref(0);
const glide = ref(false);
const MIN = 0.25;
const MAX = 1.5;
function fitScale() {
	const v = vp.value?.getBoundingClientRect();
	if (!v || !stage.value || !stage.value.offsetWidth) return MIN;
	return Math.min(
		(v.width - 64) / stage.value.offsetWidth,
		(v.height - 96) / stage.value.offsetHeight,
		1,
	);
}
const clamp = (v: number) => Math.min(MAX, Math.max(Math.max(MIN, fitScale()), v));
const reduced =
	typeof window !== "undefined" &&
	window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;

let glideTimer: any;
let touched = false;
function animate(fn: () => void) {
	touched = true;
	if (!reduced) {
		glide.value = true;
		clearTimeout(glideTimer);
		glideTimer = setTimeout(() => (glide.value = false), 380);
	}
	fn();
}

const stageStyle = computed(() => ({
	transform: `translate(${tx.value}px, ${ty.value}px) scale(${s.value})`,
	transformOrigin: "0 0",
	transition: glide.value ? "transform 360ms cubic-bezier(0.32, 0.72, 0, 1)" : "none",
}));

// The dot grid moves and scales with the chart, so dragging feels like moving paper.
const paper = computed(() => {
	const g = 20 * s.value;
	return {
		backgroundImage:
			"radial-gradient(circle, var(--outline-gray-2, #e5e5e5) 1px, transparent 1.2px)",
		backgroundSize: `${g}px ${g}px`,
		backgroundPosition: `${tx.value}px ${ty.value}px`,
	};
});

function box(id: string) {
	const el = stage.value?.querySelector(`[data-node="${id}"]`) as HTMLElement | null;
	if (!el || !stage.value) return null;
	const r = el.getBoundingClientRect();
	const st = stage.value.getBoundingClientRect();
	const k = st.width / stage.value.offsetWidth || 1;
	return { x: (r.left - st.left) / k, y: (r.top - st.top) / k, w: r.width / k, h: r.height / k };
}

function center(id: string, zoom?: number) {
	const b = box(id);
	const v = vp.value?.getBoundingClientRect();
	if (!b || !v) return;
	const ns = clamp(zoom ?? s.value);
	animate(() => {
		s.value = ns;
		tx.value = v.width / 2 - (b.x + b.w / 2) * ns;
		ty.value = v.height * 0.4 - (b.y + b.h / 2) * ns;
	});
}

const homeScale = () => ((vp.value?.getBoundingClientRect().width ?? 1024) < 640 ? 0.8 : 1);

// Brings the root into view at `zoom` (or the current zoom): top centre when the chart grows
// down, left middle when it grows right.
function showRoot(zoom?: number) {
	const b = box(ROOT.value);
	const v = vp.value?.getBoundingClientRect();
	if (!b || !v) return;
	const ns = zoom ?? s.value;
	animate(() => {
		s.value = ns;
		if (orientation.value === "horizontal") {
			tx.value = 64 - b.x * ns;
			ty.value = v.height / 2 - (b.y + b.h / 2) * ns;
		} else {
			tx.value = v.width / 2 - (b.x + b.w / 2) * ns;
			ty.value = 88 - b.y * ns;
		}
	});
}

function fit() {
	const v = vp.value?.getBoundingClientRect();
	if (!v || !stage.value) return;
	const w = stage.value.offsetWidth;
	const h = stage.value.offsetHeight;
	// Fit may go below the zoom floor: a wide chart has to fit whole.
	const ns = Math.min((v.width - 64) / w, (v.height - 96) / h, 1);
	animate(() => {
		s.value = ns;
		tx.value = (v.width - w * ns) / 2;
		ty.value = Math.max(24, (v.height - h * ns) / 2);
	});
}

function zoomAt(factor: number, cx?: number, cy?: number) {
	const v = vp.value?.getBoundingClientRect();
	if (!v) return;
	const x = cx ?? v.width / 2;
	const y = cy ?? v.height / 2;
	const ns = clamp(s.value * factor);
	const r = ns / s.value;
	tx.value = x - (x - tx.value) * r;
	ty.value = y - (y - ty.value) * r;
	s.value = ns;
}
const zoomBy = (f: number) => animate(() => zoomAt(f));

function wheel(e: WheelEvent) {
	touched = true;
	if (e.ctrlKey || e.metaKey) {
		const v = vp.value?.getBoundingClientRect();
		if (v) zoomAt(Math.exp(-e.deltaY * 0.01), e.clientX - v.left, e.clientY - v.top);
	} else {
		tx.value -= e.deltaX;
		ty.value -= e.deltaY;
	}
}

// Inside a shadow root `e.target` is the island's host, so the real target is first on the path.
const inner = (e: Event) => (e.composedPath()[0] as HTMLElement) ?? (e.target as HTMLElement);

let drag: { x: number; y: number; tx: number; ty: number; moved: boolean } | null = null;
const dragging = ref(false);
function down(e: PointerEvent) {
	if (e.button !== 0 || inner(e).closest("button, a, input, [data-panel]")) return;
	drag = { x: e.clientX, y: e.clientY, tx: tx.value, ty: ty.value, moved: false };
	vp.value?.setPointerCapture(e.pointerId);
}
function move(e: PointerEvent) {
	if (!drag) return;
	const dx = e.clientX - drag.x;
	const dy = e.clientY - drag.y;
	if (!drag.moved && Math.hypot(dx, dy) < 3) return;
	drag.moved = true;
	touched = true;
	dragging.value = true;
	tx.value = drag.tx + dx;
	ty.value = drag.ty + dy;
}
function up() {
	// A click on bare paper (no drag) lets go of the selected person.
	if (drag && !drag.moved && selected.value) emit("clear");
	drag = null;
	dragging.value = false;
}

function key(e: KeyboardEvent) {
	if (inner(e).closest("input")) return;
	if (e.key === "Escape" && selected.value) return emit("clear");
	const step = 80;
	const map: Record<string, () => void> = {
		"+": () => zoomBy(1.2),
		"=": () => zoomBy(1.2),
		"-": () => zoomBy(1 / 1.2),
		"0": fit,
		ArrowLeft: () => animate(() => (tx.value += step)),
		ArrowRight: () => animate(() => (tx.value -= step)),
		ArrowUp: () => animate(() => (ty.value += step)),
		ArrowDown: () => animate(() => (ty.value -= step)),
	};
	if (map[e.key]) {
		e.preventDefault();
		map[e.key]();
	}
}

// ---- the tree ------------------------------------------------------------------------
async function toggle(id: string) {
	touched = true;
	const before = box(id);
	const next = new Set(expanded.value);
	next.has(id) ? next.delete(id) : next.add(id);
	expanded.value = next;
	await nextTick();
	const after = box(id);
	if (before && after) {
		tx.value -= (after.x - before.x) * s.value;
		ty.value -= (after.y - before.y) * s.value;
	}
}

const select = (id: string) => emit("select", id);

async function reveal(id: string, zoom = 0.9) {
	expanded.value = new Set([...expanded.value, ...chainOf(id)]);
	await nextTick();
	center(id, Math.max(s.value, zoom));
}

async function openTeam(id: string) {
	if (!expanded.value.has(id)) await toggle(id);
	await nextTick();
	center(id);
}

const allOpen = computed(() =>
	PEOPLE.value.every((p) => !reportsOf(p.id).length || expanded.value.has(p.id)),
);
// Expand all keeps your zoom; Fit is the way to see everything. Collapse all starts over.
async function toggleAll() {
	const opening = !allOpen.value;
	expanded.value = opening
		? new Set(PEOPLE.value.filter((p) => reportsOf(p.id).length).map((p) => p.id))
		: new Set(ROOTS.value);
	await nextTick();
	if (selected.value && !box(selected.value)) emit("clear");
	showRoot(opening ? undefined : homeScale());
}

async function setOrientation(value: string | number) {
	if (value === orientation.value) return;
	orientation.value = value as Orientation;
	try {
		localStorage.setItem(ORIENTATION_KEY, orientation.value);
	} catch {}
	await nextTick();
	selBox.value = selected.value ? box(selected.value) : null;
	if (selected.value) center(selected.value);
	else showRoot();
}

provide("org", { byId, reportsOf, expanded, selected, you, toggle, select, orientation });
defineExpose({ reveal, openTeam });

// Search flies to a person and opens them.
const pick = ref<string | null>(null);
const query = ref("");
const options = computed(() =>
	PEOPLE.value.map((p) => ({ label: p.name, value: p.id, description: deptOf(p.id) })),
);
function onPick(id: string | null) {
	if (!id) return;
	reveal(id);
	emit("select", id);
	pick.value = null;
	query.value = "";
}

// Centre on the manager, not on you: you sit among your peers, your team below.
function place() {
	const wide = orientation.value === "horizontal";
	const target = focus.value || (wide ? start : byId.value[start]?.manager || start);
	const b = box(target);
	const v = vp.value?.getBoundingClientRect();
	if (!b || !v || !v.width) return;
	s.value = homeScale();
	if (wide) {
		const r = box(ROOT.value) ?? b;
		tx.value = Math.min(64 - r.x * s.value, v.width * 0.4 - (b.x + b.w / 2) * s.value);
		ty.value = v.height / 2 - (b.y + b.h / 2) * s.value;
		return;
	}
	tx.value = v.width / 2 - (b.x + b.w / 2) * s.value;
	ty.value = focus.value
		? v.height * 0.35 - (b.y + b.h / 2) * s.value
		: Math.min(16, 96 - b.y * s.value);
}

// ---- the card beside the selected person -------------------------------------------
// It sits to the right of the node (left if there is no room) and rides along as you pan.
const vpSize = ref({ w: 0, h: 0 });
const selBox = ref<ReturnType<typeof box>>(null);
watch(
	[selected, expanded, orientation],
	async () => {
		await nextTick();
		selBox.value = selected.value ? box(selected.value) : null;
	},
	{ immediate: true },
);
const CARD_W = 288;
const CARD_H = 250;
const cardStyle = computed(() => {
	const b = selBox.value;
	const { w, h } = vpSize.value;
	if (!b || !w) return null;
	if (w < 640) return { left: "16px", right: "16px", bottom: "68px" };
	const x = tx.value + b.x * s.value;
	const y = ty.value + b.y * s.value;
	const nw = b.w * s.value;
	// Left to right, their team sits to the right, so the card opens below the node (above if no room).
	if (orientation.value === "horizontal") {
		const nh = b.h * s.value;
		const below = y + nh + 8;
		const top = below + CARD_H > h - 16 ? y - CARD_H - 8 : below;
		const left = Math.min(Math.max(16, x), w - CARD_W - 16);
		return { left: `${left}px`, top: `${Math.max(64, top)}px`, width: `${CARD_W}px` };
	}
	let left = x + nw + 12;
	if (left + CARD_W > w - 16) left = x - CARD_W - 12;
	left = Math.min(Math.max(16, left), w - CARD_W - 16);
	const top = Math.min(Math.max(64, y), Math.max(64, h - CARD_H - 16));
	return { left: `${left}px`, top: `${top}px`, width: `${CARD_W}px` };
});

let ro: ResizeObserver | undefined;
onMounted(async () => {
	await nextTick();
	place();
	ro = new ResizeObserver(() => {
		const v = vp.value?.getBoundingClientRect();
		if (v) vpSize.value = { w: v.width, h: v.height };
		if (!touched) place();
	});
	if (stage.value) ro.observe(stage.value);
	if (vp.value) ro.observe(vp.value);
});
onBeforeUnmount(() => {
	clearTimeout(glideTimer);
	ro?.disconnect();
});
watch(focus, (id) => id && reveal(id));
watch(
	() => known(props.person),
	(id) => id && (pickedId.value = id),
);
</script>

<template>
	<div
		ref="vp"
		tabindex="0"
		role="application"
		:aria-label="__('Org chart. Drag to move, plus and minus to zoom, 0 to fit.')"
		class="relative h-full w-full touch-none select-none overflow-hidden bg-surface-base outline-none"
		:class="dragging ? 'cursor-grabbing' : 'cursor-grab'"
		:style="paper"
		@pointerdown="down"
		@pointermove="move"
		@pointerup="up"
		@pointercancel="up"
		@wheel.prevent="wheel"
		@keydown="key"
	>
		<div
			ref="stage"
			class="absolute left-0 top-0 inline-flex flex-col items-center p-10"
			:class="orientation === 'horizontal' && '!pr-28'"
			:style="stageStyle"
		>
			<div
				class="flex items-start gap-16"
				:class="orientation === 'horizontal' && 'flex-col'"
			>
				<OrgNode v-for="id in ROOTS" :key="id" :id="id" />
			</div>
		</div>

		<Transition
			enter-active-class="transition duration-150"
			enter-from-class="opacity-0 translate-y-1"
			leave-active-class="transition duration-100"
			leave-to-class="opacity-0"
		>
			<div
				v-if="cardStyle"
				:key="selected"
				data-panel
				class="absolute z-10 cursor-auto"
				:style="cardStyle"
			>
				<OrgPersonCard :id="selected" @close="emit('clear')" @team="openTeam" />
			</div>
		</Transition>

		<div
			data-panel
			class="absolute left-4 right-4 top-4 rounded-4 bg-surface-base sm:right-auto sm:w-72"
		>
			<Combobox
				class="w-full"
				variant="outline"
				v-model="pick"
				v-model:query="query"
				:options="options"
				:placeholder="__('Find a person')"
				@update:model-value="onPick"
			/>
		</div>

		<div
			data-panel
			class="absolute bottom-4 left-4 flex items-center gap-0.5 rounded-5 border border-outline-gray-2 bg-surface-base p-1"
		>
			<Tooltip :text="__('Zoom out')"
				><Button
					variant="ghost"
					icon="lucide-minus"
					:aria-label="__('Zoom out')"
					@click="zoomBy(1 / 1.2)"
			/></Tooltip>
			<Button
				variant="ghost"
				class="min-w-12 tabular-nums"
				:label="`${Math.round(s * 100)}%`"
				:aria-label="__('Reset zoom to 100%')"
				@click="animate(() => zoomAt(1 / s))"
			/>
			<Tooltip :text="__('Zoom in')"
				><Button
					variant="ghost"
					icon="lucide-plus"
					:aria-label="__('Zoom in')"
					@click="zoomBy(1.2)"
			/></Tooltip>
			<Divider orientation="vertical" class="mx-1 !h-4" />
			<Tooltip :text="__('Fit to screen')"
				><Button
					variant="ghost"
					icon="lucide-maximize"
					:aria-label="__('Fit to screen')"
					@click="fit"
			/></Tooltip>
			<Tooltip v-if="you" :text="__('Find me')"
				><Button
					variant="ghost"
					icon="lucide-locate-fixed"
					:aria-label="__('Find me')"
					@click="reveal(you)"
			/></Tooltip>
			<Divider orientation="vertical" class="mx-1 hidden !h-4 sm:block" />
			<Button
				class="hidden sm:inline-flex"
				variant="ghost"
				:icon-left="allOpen ? 'lucide-chevrons-down-up' : 'lucide-chevrons-up-down'"
				:label="allOpen ? __('Collapse all') : __('Expand all')"
				@click="toggleAll"
			/>
			<Divider orientation="vertical" class="mx-1 !h-4" />
			<TabButtons
				:model-value="orientation"
				:options="orientations"
				:aria-label="__('Chart orientation')"
				@update:model-value="setOrientation"
			/>
		</div>
	</div>
</template>
