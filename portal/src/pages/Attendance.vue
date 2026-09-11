<template>
	<PageBody :loading="attendanceData.loading && !attendanceData.data">
		<PageHead title="Attendance" subtitle="Your month at a glance">
			<template #actions>
				<!--
					Label first, then the arrows as an adjacent pair: sandwiching it between
					them splits one control in two and makes the arrows read as unrelated.
					It stays beside them so the change is still where the eye is.
				-->
				<div
					class="flex items-center gap-2"
					role="group"
					aria-label="Month"
					@keydown.left.prevent="step(-1)"
					@keydown.right.prevent="step(1)"
				>
					<span class="nums text-base-semibold text-ink-gray-8" aria-live="polite">
						{{ d?.month_label || "—" }}
					</span>
					<div class="flex items-center gap-1">
						<Button
							ref="prevBtn"
							variant="subtle"
							icon="lucide-chevron-left"
							label="Previous month"
							:disabled="!d?.prev_month"
							@click="step(-1)"
						/>
						<Button
							ref="nextBtn"
							variant="subtle"
							icon="lucide-chevron-right"
							label="Next month"
							:disabled="!d?.next_month"
							@click="step(1)"
						/>
					</div>
				</div>
				<Button variant="solid" @click="showNew = true">Regularise</Button>
			</template>
		</PageHead>

		<template v-if="d">
			<StatTiles :tiles="tiles" />

			<DashGrid>
				<template #main>
					<SectionCard :title="d.month_label">
						<MonthCalendar :days="d.days" />
					</SectionCard>
				</template>

				<template #side>
					<SectionCard title="Today">
						<template #action>
							<StatusBadge
								:status="d.today.checked_in ? 'On shift' : 'Not checked in'"
								:label="d.today.checked_in ? 'On shift' : 'Not checked in'"
							/>
						</template>
						<dl class="flex flex-col">
							<FieldRow
								label="Checked in"
								:value="d.today.since ? time(d.today.since) : ''"
								nums
							/>
							<FieldRow label="Source" :value="d.today.device || 'Web'" />
						</dl>
					</SectionCard>

					<SectionCard title="Needs Action" :padded="false">
						<template #action>
							<StatusBadge
								v-if="d.stats.unmarked"
								status="unmarked"
								:label="String(d.stats.unmarked)"
							/>
						</template>
						<ul v-if="d.unmarked.length">
							<li
								v-for="u in d.unmarked"
								:key="u.date"
								class="flex items-center justify-between gap-3 border-b border-outline-gray-1 px-3.5 py-2.5 last:border-0"
							>
								<div>
									<div class="text-p-base text-ink-gray-8">
										{{ date(u.date) }}
									</div>
									<div class="text-base text-ink-gray-5">
										No attendance marked
									</div>
								</div>
								<Button
									class="shrink-0"
									variant="ghost"
									label="Regularise"
									@click="showNew = true"
								/>
							</li>
						</ul>
						<div v-else class="px-3.5 pb-3.5">
							<EmptyState message="Every past day this month is accounted for." />
						</div>
					</SectionCard>

					<SectionCard title="Shift" readonly-label="HR-owned">
						<dl class="flex flex-col">
							<FieldRow label="Assigned" :value="d.shift?.name" locked />
							<FieldRow label="Timing" :value="shiftTiming(d.shift)" locked nums />
							<FieldRow label="Weekly off" :value="d.weekly_off" locked />
						</dl>
					</SectionCard>
				</template>
			</DashGrid>
		</template>
	</PageBody>

	<RequestDialog v-model:open="showNew" type="attendance" @saved="attendanceData.fetch()" />
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from "vue";
import { Button } from "frappe-ui";

import PageBody from "@/components/PageBody.vue";
import PageHead from "@/components/PageHead.vue";
import DashGrid from "@/components/DashGrid.vue";
import SectionCard from "@/components/SectionCard.vue";
import StatTiles from "@/components/StatTiles.vue";
import StatusBadge from "@/components/StatusBadge.vue";
import FieldRow from "@/components/FieldRow.vue";
import EmptyState from "@/components/EmptyState.vue";
import MonthCalendar from "@/components/MonthCalendar.vue";
import RequestDialog from "@/components/RequestDialog.vue";

import { attendanceData } from "@/data/portal";
import { date, shiftTiming, time } from "@/utils/format";

const showNew = ref(false);
const d = computed(() => attendanceData.data);

const tiles = computed(() => {
	const s = d.value?.stats || {};
	return [
		{
			label: "Present",
			value: s.present ?? 0,
			hint: `of ${s.working_days ?? 0} working days`,
		},
		{ label: "On Leave", value: s.on_leave ?? 0, hint: s.absent ? `${s.absent} absent` : "" },
		{
			label: "Unmarked",
			value: s.unmarked ?? 0,
			hint: s.unmarked ? "needs action" : "all accounted for",
		},
		{ label: "Avg Hours", value: s.avg_hours ?? 0, hint: "per marked day" },
	];
});

const prevBtn = ref(null);
const nextBtn = ref(null);

/**
 * Stepping to the current month disables the next arrow, which would drop focus
 * to the body mid-keystroke, so focus falls back to the arrow still enabled.
 */
async function step(dir) {
	const month = dir < 0 ? d.value?.prev_month : d.value?.next_month;
	if (!month) return;

	await attendanceData.fetch({ month });
	await nextTick();

	const el = (r) => r?.$el ?? r;
	const moved = el(dir < 0 ? prevBtn.value : nextBtn.value);
	const other = el(dir < 0 ? nextBtn.value : prevBtn.value);
	(moved?.disabled ? other : moved)?.focus();
}

onMounted(() => attendanceData.fetch());
</script>
