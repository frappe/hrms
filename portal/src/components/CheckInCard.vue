<template>
	<SectionCard>
		<div class="flex flex-wrap items-start justify-between gap-3">
			<div class="min-w-0">
				<p class="text-base text-ink-gray-5">
					{{ statusLine }}
				</p>
				<p class="nums mt-0.5 text-4xl-semibold leading-tight text-ink-gray-9">
					{{ checkin.checked_in ? ticker : "—" }}
				</p>
				<div class="mt-1.5 flex flex-wrap items-center gap-2">
					<StatusBadge
						:status="checkin.checked_in ? 'On shift' : 'Not checked in'"
						:label="checkin.checked_in ? 'On shift' : 'Not checked in'"
					/>
					<span v-if="timing" class="text-base text-ink-gray-5">{{ timing }}</span>
				</div>
			</div>
			<div class="flex shrink-0 gap-2">
				<Button variant="subtle" @click="$router.push('/attendance')">View Log</Button>
				<Button variant="solid" :loading="saving" @click="toggle">
					{{ checkin.checked_in ? "Check Out" : "Check In" }}
				</Button>
			</div>
		</div>

		<!--
			Attendance status per day, without a second query. Each day opens its
			own detail below, so this is a toolbar: one Tab stop for the week and
			arrow keys within it, rather than seven stops.
		-->
		<div
			class="grid grid-cols-7 gap-1.5"
			role="toolbar"
			aria-label="This week"
			@keydown="onKey"
		>
			<button
				v-for="(day, i) in week"
				:key="day.date"
				ref="pills"
				type="button"
				:title="`${date(day.date, 'dddd D MMMM')}, ${label(day)}`"
				class="flex cursor-pointer flex-col items-center gap-1 rounded-4 p-1 transition-colors hover:bg-surface-gray-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
				:tabindex="i === activeIndex ? 0 : -1"
				:aria-pressed="selected === day.date"
				:aria-label="`${date(day.date, 'dddd D MMMM')}, ${label(day)}`"
				@click="select(day)"
			>
				<span class="text-[10px] text-ink-gray-4">{{ day.label }}</span>
				<span
					class="h-6 w-full rounded-4"
					:class="[
						dayClass(day),
						day.is_today && 'ring-1 ring-inset ring-outline-gray-4',
					]"
				/>
				<!--
					Selection is an underline, not a surface: hover already owns the
					background and today owns the ring on the bar, so a third state
					needs its own channel. Geometry and colour are TabList's, since
					this is the same idea: one active item in a strip.
				-->
				<span
					class="-mb-1 h-px w-full transition-colors"
					:class="
						selected === day.date ? 'bg-[var(--outline-gray-8)]' : 'bg-transparent'
					"
					aria-hidden="true"
				/>
			</button>
		</div>

		<div
			v-if="day"
			class="rounded-6 border border-outline-gray-1 bg-surface-gray-1 px-3 py-2.5"
		>
			<div class="flex flex-wrap items-center justify-between gap-2">
				<div class="flex min-w-0 flex-wrap items-center gap-2">
					<span class="text-base-semibold text-ink-gray-8">
						{{ date(day.date, "dddd, D MMMM") }}
					</span>
					<StatusBadge :status="label(day)" :label="label(day)" />
					<span v-if="reason" class="truncate text-base text-ink-gray-5">{{
						reason
					}}</span>
				</div>
				<Button
					variant="ghost"
					icon="lucide-x"
					label="Close day"
					@click="selected = null"
				/>
			</div>
			<dl class="mt-2 grid grid-cols-2 gap-x-4 gap-y-2 sm:grid-cols-4">
				<div v-for="f in facts" :key="f.label">
					<dt class="text-sm text-ink-gray-5">{{ f.label }}</dt>
					<dd class="nums truncate text-base text-ink-gray-8" :title="f.value">
						{{ f.value }}
					</dd>
				</div>
			</dl>

			<!--
				Every punch on the day, not just the first and last: a day with a
				lunch break reads as four entries, and the gap between them is the
				only place that shows.
			-->
			<div class="mt-2.5 border-t border-outline-gray-1 pt-2.5">
				<p class="text-sm text-ink-gray-5">Check-ins</p>
				<ul v-if="day.logs?.length" class="mt-1.5 flex flex-wrap gap-1.5">
					<li
						v-for="(log, i) in day.logs"
						:key="i"
						class="flex items-center gap-1.5 rounded-full border border-outline-gray-1 bg-surface-base py-0.5 pl-1.5 pr-2.5"
					>
						<span
							class="h-1.5 w-1.5 rounded-full"
							:class="
								log.log_type === 'IN' ? 'bg-surface-green-3' : 'bg-surface-gray-5'
							"
							aria-hidden="true"
						/>
						<span class="text-sm text-ink-gray-6">{{ log.log_type }}</span>
						<span class="nums text-sm text-ink-gray-8">{{ time(log.time) }}</span>
					</li>
				</ul>
				<p v-else class="mt-1 text-base text-ink-gray-5">
					{{ day.is_future ? "Nothing recorded yet." : "No check-ins on this day." }}
				</p>
			</div>
		</div>
	</SectionCard>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from "vue";
import { Button } from "frappe-ui";

import SectionCard from "@/components/SectionCard.vue";
import StatusBadge from "@/components/StatusBadge.vue";
import { date, elapsed, shiftTiming, time } from "@/utils/format";
import { markCheckin } from "@/data/portal";
import { errorMessage, notifyError, notifySuccess } from "@/utils/toast";

const props = defineProps({
	checkin: { type: Object, default: () => ({}) },
	week: { type: Array, default: () => [] },
});
const emit = defineEmits(["changed"]);

const ticker = ref("00:00:00");
const saving = ref(false);
const selected = ref(null);
const pills = ref([]);
const focused = ref(null);
let timer = null;

const timing = computed(() => {
	const t = shiftTiming(props.checkin.shift);
	return props.checkin.shift ? `${props.checkin.shift.name}, ${t}` : null;
});

const statusLine = computed(() =>
	props.checkin.checked_in
		? `Checked in at ${time(props.checkin.since)}`
		: "You have not checked in today",
);

const day = computed(() => props.week.find((d) => d.date === selected.value) || null);

/** Arrow keys start from today unless the employee has moved the focus. */
const activeIndex = computed(() => {
	if (focused.value !== null) return focused.value;
	const i = props.week.findIndex((d) => d.is_today);
	return i === -1 ? 0 : i;
});

/** What the day amounts to, whether or not attendance was ever marked. */
function label(d) {
	if (d.status) return d.status;
	if (d.weekly_off) return "Weekly off";
	if (d.holiday) return "Holiday";
	return d.is_future ? "Upcoming" : "Not marked";
}

const reason = computed(() => day.value?.leave_type || day.value?.holiday || "");

const facts = computed(() => {
	const d = day.value;
	if (!d) return [];
	return [
		{ label: "In", value: time(d.in_time) },
		{ label: "Out", value: time(d.out_time) },
		{ label: "Hours", value: d.hours ? `${d.hours} h` : "—" },
		{
			label: "Shift",
			value: d.shift ? `${d.shift.name}, ${shiftTiming(d.shift)}` : "—",
		},
	];
});

function select(d) {
	selected.value = selected.value === d.date ? null : d.date;
}

function onKey(e) {
	const step = { ArrowLeft: -1, ArrowRight: 1 }[e.key];
	let next;
	if (step) next = activeIndex.value + step;
	else if (e.key === "Home") next = 0;
	else if (e.key === "End") next = props.week.length - 1;
	else return;

	e.preventDefault();
	focused.value = Math.max(0, Math.min(props.week.length - 1, next));
	nextTick(() => pills.value[focused.value]?.focus());
}

function tick() {
	ticker.value = props.checkin.checked_in ? elapsed(props.checkin.since) : "00:00:00";
}

async function toggle() {
	saving.value = true;
	try {
		await markCheckin.submit({ log_type: props.checkin.checked_in ? "OUT" : "IN" });
		notifySuccess(props.checkin.checked_in ? "Checked out" : "Checked in");
		emit("changed");
	} catch (e) {
		notifyError("Could not record that", errorMessage(e, "Try again in a moment."));
	} finally {
		saving.value = false;
	}
}

function dayClass(d) {
	switch (d.status) {
		case "Present":
		case "Work From Home":
			return "bg-surface-green-2";
		case "Half Day":
			return "bg-surface-amber-2";
		case "On Leave":
			return "bg-surface-blue-2";
		case "Absent":
			return "bg-surface-red-2";
		default:
			return "bg-surface-gray-3";
	}
}

onMounted(() => {
	tick();
	timer = setInterval(tick, 1000);
});
onBeforeUnmount(() => clearInterval(timer));
</script>
