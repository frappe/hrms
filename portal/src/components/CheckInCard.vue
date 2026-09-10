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

		<!-- attendance status per day, without a second query -->
		<div class="grid grid-cols-7 gap-1.5">
			<div v-for="d in week" :key="d.date" class="flex flex-col items-center gap-1">
				<span class="text-[10px] text-ink-gray-4">{{ d.label }}</span>
				<span
					class="h-6 w-full rounded-4"
					:class="[dayClass(d), d.is_today && 'ring-1 ring-inset ring-outline-gray-4']"
					:title="d.status || 'Not marked'"
				/>
			</div>
		</div>
	</SectionCard>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { Button } from "frappe-ui";

import SectionCard from "@/components/SectionCard.vue";
import StatusBadge from "@/components/StatusBadge.vue";
import { elapsed, shiftTiming, time } from "@/utils/format";
import { markCheckin } from "@/data/portal";
import { errorMessage, notifyError, notifySuccess } from "@/utils/toast";

const props = defineProps({
	checkin: { type: Object, default: () => ({}) },
	week: { type: Array, default: () => [] },
});
const emit = defineEmits(["changed"]);

const ticker = ref("00:00:00");
const saving = ref(false);
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
