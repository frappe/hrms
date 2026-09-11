<template>
	<PageBody :loading="appraisalsData.loading && !appraisalsData.data">
		<PageHead title="Appraisals" subtitle="Your reviews and how your pay has moved" />

		<template v-if="d">
			<StatTiles :tiles="tiles" />

			<SectionCard title="Review History" :padded="false">
				<DataTable
					:columns="reviewCols"
					:rows="d.appraisals"
					clickable
					empty-message="You have not been appraised yet."
					@row-click="open"
				>
					<template #cell-cycle="{ row }">
						<span class="text-ink-gray-8">{{ row.cycle }}</span>
					</template>
					<template #cell-year="{ row }">
						<span class="nums text-ink-gray-5">{{ row.year || "—" }}</span>
					</template>
					<template #cell-final_score="{ row }">
						<Score :value="row.final_score" strong />
					</template>
					<template #cell-self_score="{ row }"
						><Score :value="row.self_score"
					/></template>
					<template #cell-feedback_score="{ row }">
						<Score :value="row.feedback_score" />
					</template>
					<template #cell-status="{ row }"
						><StatusBadge :status="row.status"
					/></template>
				</DataTable>
			</SectionCard>

			<SectionCard title="Pay Revisions" :padded="false">
				<template #action>
					<StatusBadge
						v-if="d.growth.total_pct"
						status="approved"
						:label="`${signed(d.growth.total_pct)}% since ${date(
							d.growth.from_date,
							'MMM YYYY',
						)}`"
					/>
				</template>
				<DataTable
					:columns="payCols"
					:rows="d.compensation"
					empty-message="No salary structure has been assigned yet."
				>
					<template #cell-from_date="{ row }">
						<span class="nums text-ink-gray-8">{{ date(row.from_date) }}</span>
					</template>
					<template #cell-base="{ row }">{{ money(row.base) }}</template>
					<template #cell-annual="{ row }">
						<span class="font-semibold text-ink-gray-9">{{ money(row.annual) }}</span>
					</template>
					<!--
						The first revision has nothing to grow from, so it shows a dash
						rather than a misleading 0%.
					-->
					<template #cell-change="{ row }">
						<span v-if="row.change_pct === null" class="text-ink-gray-4">—</span>
						<span v-else class="nums" :class="toneOf(row.change_pct)">
							{{ signed(row.change_pct) }}%
						</span>
					</template>
				</DataTable>
			</SectionCard>
		</template>
	</PageBody>
</template>

<script setup>
import { computed, onMounted } from "vue";
import { useRouter } from "vue-router";

import PageBody from "@/components/PageBody.vue";
import PageHead from "@/components/PageHead.vue";
import SectionCard from "@/components/SectionCard.vue";
import DataTable from "@/components/DataTable.vue";
import StatTiles from "@/components/StatTiles.vue";
import StatusBadge from "@/components/StatusBadge.vue";
import Score from "@/components/Score.vue";

import { appraisalsData } from "@/data/portal";
import { date, money } from "@/utils/format";

const reviewCols = [
	{ key: "cycle", label: "Cycle", primary: true },
	{ key: "year", label: "Year", nums: true, muted: true, hideOnMobile: true },
	{ key: "self_score", label: "Self", align: "right", nums: true, hideOnMobile: true },
	{ key: "feedback_score", label: "Feedback", align: "right", nums: true, hideOnMobile: true },
	{ key: "final_score", label: "Final", align: "right", nums: true },
	{ key: "status", label: "Status", align: "right", badge: true },
];

const payCols = [
	{ key: "from_date", label: "Effective", primary: true },
	{ key: "base", label: "Monthly", align: "right", nums: true, muted: true, hideOnMobile: true },
	{ key: "annual", label: "CTC", align: "right", nums: true },
	{ key: "change", label: "Change", align: "right", nums: true },
];

const router = useRouter();
const d = computed(() => appraisalsData.data);

const tiles = computed(() => {
	const s = d.value?.stats || {};
	return [
		{
			label: "Latest score",
			value: s.latest_score ? `${s.latest_score} / 5` : "—",
			hint: s.latest_cycle || "No review yet",
		},
		{
			label: "Average score",
			value: s.average_score ? `${s.average_score} / 5` : "—",
			hint: s.reviews ? `${s.reviews} review${s.reviews === 1 ? "" : "s"}` : "",
		},
		{
			label: "Current CTC",
			value: money(s.current_ctc, { compact: true }),
			hint: s.current_since ? `since ${date(s.current_since, "MMM YYYY")}` : "",
		},
		{
			label: "Total growth",
			value: d.value?.growth?.total_pct ? `${signed(d.value.growth.total_pct)}%` : "—",
			hint: d.value?.growth?.annual_pct
				? `${signed(d.value.growth.annual_pct)}% a year`
				: "",
		},
	];
});

function signed(n) {
	return `${n > 0 ? "+" : ""}${n}`;
}

function toneOf(pct) {
	if (pct > 0) return "text-ink-green-3";
	return pct < 0 ? "text-ink-red-3" : "text-ink-gray-6";
}

function open(row) {
	router.push(`/appraisals/${encodeURIComponent(row.name)}`);
}

onMounted(() => appraisalsData.fetch());
</script>
