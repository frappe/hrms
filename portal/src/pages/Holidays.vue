<template>
	<PageBody :loading="holidaysData.loading && !holidaysData.data">
		<PageHead title="Holidays" :subtitle="d?.list_name || 'No holiday list assigned'" />

		<template v-if="d">
			<StatTiles :tiles="tiles" />

			<DashGrid>
				<template #main>
					<SectionCard title="Holiday List" readonly-label="HR-owned" :padded="false">
						<DataTable
							:columns="cols"
							:rows="d.holidays"
							id-key="date"
							empty-message="No holidays configured for your list."
						>
							<template #cell-date="{ row }">
								<span :class="row.is_past && 'text-ink-gray-5'">{{
									date(row.date)
								}}</span>
							</template>
							<template #cell-weekday="{ row }">
								<span class="text-ink-gray-5">{{ row.weekday }}</span>
							</template>
							<template #cell-description="{ row }">
								<span :class="row.is_past && 'text-ink-gray-5'">{{
									row.description
								}}</span>
							</template>
							<template #cell-flag="{ row }">
								<StatusBadge
									v-if="row.falls_on_off"
									status="weekly off"
									label="Falls on a weekly off"
								/>
								<StatusBadge v-else-if="row.is_past" status="taken" label="Past" />
								<StatusBadge v-else status="available" label="Upcoming" />
							</template>
						</DataTable>
					</SectionCard>
				</template>

				<template #side>
					<SectionCard title="Your Calendar" readonly-label="HR-owned">
						<dl class="flex flex-col">
							<FieldRow label="Holiday list" :value="d.list_name" locked />
							<FieldRow label="Weekly off" :value="d.weekly_off" locked />
							<FieldRow label="Location" :value="d.branch" locked />
						</dl>
					</SectionCard>

					<SectionCard v-if="d.stats.next" title="Next Holiday">
						<div class="flex flex-col gap-0.5">
							<span class="text-p-base font-semibold text-ink-gray-9">
								{{ d.stats.next.description }}
							</span>
							<span class="nums text-base text-ink-gray-5">
								{{ date(d.stats.next.date) }} · {{ d.stats.next.weekday }}
							</span>
						</div>
					</SectionCard>
				</template>
			</DashGrid>
		</template>
	</PageBody>
</template>

<script setup>
import { computed, onMounted } from "vue";

import PageBody from "@/components/PageBody.vue";
import PageHead from "@/components/PageHead.vue";
import DashGrid from "@/components/DashGrid.vue";
import SectionCard from "@/components/SectionCard.vue";
import DataTable from "@/components/DataTable.vue";
import StatTiles from "@/components/StatTiles.vue";
import StatusBadge from "@/components/StatusBadge.vue";
import FieldRow from "@/components/FieldRow.vue";

import { holidaysData } from "@/data/portal";
import { date } from "@/utils/format";

const cols = [
	{ key: "date", label: "Date", nums: true },
	{ key: "weekday", label: "Day", hideOnMobile: true },
	{ key: "description", label: "Occasion", primary: true },
	{ key: "flag", label: "", align: "right", badge: true },
];

const d = computed(() => holidaysData.data);

/** Remaining is the useful figure. Total is trivia. */
const tiles = computed(() => {
	const s = d.value?.stats || {};
	return [
		{
			label: "Remaining",
			value: s.remaining ?? 0,
			hint: s.next ? `next ${date(s.next.date)}` : "",
		},
		{ label: "Total This Year", value: s.total ?? 0, hint: "excluding weekly offs" },
		{
			label: "Lost to Weekends",
			value: (d.value?.holidays || []).filter((h) => h.falls_on_off).length,
			hint: "fall on a weekly off",
		},
	];
});

onMounted(() => holidaysData.fetch());
</script>
