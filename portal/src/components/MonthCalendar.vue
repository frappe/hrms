<template>
	<div class="flex flex-col gap-3">
		<!-- month grid from md up -->
		<div class="hidden md:block">
			<div class="grid grid-cols-7 gap-1">
				<div
					v-for="d in WEEKDAYS"
					:key="d"
					class="pb-1 text-center text-base text-ink-gray-4"
				>
					{{ d }}
				</div>
				<div v-for="n in leadingBlanks" :key="`b${n}`" />
				<div
					v-for="day in days"
					:key="day.date"
					class="flex h-[52px] flex-col rounded-4 px-1.5 py-1 text-[10px]"
					:class="[
						cellClass(day),
						day.is_today && 'ring-1 ring-inset ring-outline-gray-4',
					]"
				>
					<span class="nums font-medium">{{ day.day }}</span>
					<span class="mt-auto truncate opacity-90">{{ marker(day) }}</span>
				</div>
			</div>
		</div>

		<!-- a 7 by 5 grid is unreadable at 360px, so below md it becomes a day list -->
		<ul class="md:hidden">
			<li
				v-for="day in listDays"
				:key="day.date"
				class="flex items-center justify-between gap-3 border-b border-outline-gray-1 py-2 last:border-0"
			>
				<div class="flex min-w-0 items-center gap-2.5">
					<span class="nums w-10 shrink-0 text-base text-ink-gray-5">
						{{ shortDate(day.date) }}
					</span>
					<span class="truncate text-p-base text-ink-gray-8">
						{{ day.holiday || day.leave_type || day.status || "Not marked" }}
					</span>
				</div>
				<span class="nums shrink-0 text-base text-ink-gray-5">
					{{ day.hours ? `${day.hours}h` : "" }}
				</span>
			</li>
		</ul>

		<div class="flex flex-wrap gap-x-3 gap-y-1.5">
			<span v-for="k in LEGEND" :key="k.label" class="flex items-center gap-1.5">
				<span class="h-2.5 w-2.5 rounded-1" :class="k.class" />
				<span class="text-[10px] text-ink-gray-5">{{ k.label }}</span>
			</span>
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue";
import { dayjs } from "@/utils/format";

const props = defineProps({ days: { type: Array, default: () => [] } });

const WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

const LEGEND = [
	{ label: "Present", class: "bg-surface-green-2" },
	{ label: "Half day", class: "bg-surface-amber-2" },
	{ label: "Leave", class: "bg-surface-blue-2" },
	{ label: "Absent", class: "bg-surface-red-2" },
	{ label: "Holiday", class: "bg-surface-gray-4" },
];

const leadingBlanks = computed(() => (props.days.length ? props.days[0].weekday : 0));

/** The list view only shows days that carry information. */
const listDays = computed(() => props.days.filter((d) => d.status || d.holiday || d.leave_type));

function cellClass(day) {
	if (day.weekly_off || (day.holiday && !day.status)) return "bg-surface-gray-3 text-ink-gray-4";
	switch (day.status) {
		case "Present":
		case "Work From Home":
			return "bg-surface-green-2 text-ink-green-6";
		case "Half Day":
			return "bg-surface-amber-2 text-ink-amber-6";
		case "On Leave":
			return "bg-surface-blue-2 text-ink-blue-6";
		case "Absent":
			return "bg-surface-red-2 text-ink-red-8";
		default:
			return "bg-surface-gray-2 text-ink-gray-5";
	}
}

function marker(day) {
	if (day.hours) return `${day.hours}h`;
	if (day.leave_type) return day.leave_type;
	if (day.holiday) return day.weekly_off ? "" : day.holiday;
	return "";
}

function shortDate(value) {
	return dayjs(value).format("D MMM");
}
</script>
