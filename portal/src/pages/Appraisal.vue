<template>
	<PageBody :loading="appraisalData.loading && !appraisalData.data">
		<template v-if="d">
			<PageHead
				:subtitle="`${dateRange(d.start_date, d.end_date)} · ${d.designation || ''}`"
				:crumbs="[{ label: 'Appraisals', to: '/appraisals' }, { label: d.cycle }]"
			>
				<template #actions>
					<StatusBadge :status="d.status" />
				</template>
			</PageHead>

			<StatTiles :tiles="tiles" />

			<DashGrid>
				<template #main>
					<!--
						KRAs are scored from linked goals; the goals table is what an
						appraisal rated by hand uses. Only one of the two is ever filled.
					-->
					<SectionCard
						v-if="d.kras.length"
						title="KRAs"
						readonly-label="Scored from goals"
						:padded="false"
					>
						<DataTable :columns="kraCols" :rows="d.kras" id-key="kra">
							<template #cell-weightage="{ row }">{{ row.weightage }}%</template>
							<template #cell-completion="{ row }">{{ row.completion }}%</template>
							<template #cell-score="{ row }"
								><Score :value="row.score" strong
							/></template>
						</DataTable>
						<TotalRow label="Goal Score" :value="`${d.goal_score} / 5`" />
					</SectionCard>

					<SectionCard
						v-if="d.goals.length"
						title="Goals"
						:readonly-label="d.rated_manually ? 'Rated by your manager' : null"
						:padded="false"
					>
						<DataTable :columns="goalCols" :rows="d.goals" id-key="kra">
							<template #cell-weightage="{ row }">{{ row.weightage }}%</template>
							<template #cell-score="{ row }"><Score :value="row.score" /></template>
							<template #cell-earned="{ row }">
								<span class="nums font-semibold text-ink-gray-9">{{
									row.earned
								}}</span>
							</template>
						</DataTable>
						<TotalRow label="Goal Score" :value="`${d.goal_score} / 5`" />
					</SectionCard>

					<SectionCard v-if="d.feedback.length" title="Feedback">
						<ul class="flex flex-col gap-3">
							<li
								v-for="f in d.feedback"
								:key="f.name"
								class="border-b border-outline-gray-1 pb-3 last:border-0 last:pb-0"
							>
								<div class="flex flex-wrap items-baseline justify-between gap-2">
									<PersonRow
										:name="f.reviewer"
										:meta="f.designation || ''"
										size="md"
									/>
									<Score :value="f.score" strong />
								</div>
								<p
									v-if="f.feedback"
									class="mt-2 whitespace-pre-line text-p-base text-ink-gray-7"
								>
									{{ f.feedback }}
								</p>
								<p v-if="f.added_on" class="mt-1 text-sm text-ink-gray-5">
									{{ date(f.added_on) }}
								</p>
							</li>
						</ul>
					</SectionCard>
				</template>

				<template #side>
					<SectionCard v-if="d.self_ratings.length" title="Self Rating">
						<dl class="flex flex-col">
							<FieldRow
								v-for="r in d.self_ratings"
								:key="r.criteria"
								:label="`${r.criteria} · ${r.weightage}%`"
								:value="`${r.rating} / 5`"
								nums
							/>
						</dl>
					</SectionCard>

					<SectionCard v-if="d.reflections" title="Your Reflections">
						<p class="whitespace-pre-line text-p-base text-ink-gray-7">
							{{ d.reflections }}
						</p>
					</SectionCard>
				</template>
			</DashGrid>
		</template>
	</PageBody>
</template>

<script setup>
import { computed, watch } from "vue";
import { useRoute } from "vue-router";

import PageBody from "@/components/PageBody.vue";
import PageHead from "@/components/PageHead.vue";
import DashGrid from "@/components/DashGrid.vue";
import SectionCard from "@/components/SectionCard.vue";
import DataTable from "@/components/DataTable.vue";
import StatTiles from "@/components/StatTiles.vue";
import StatusBadge from "@/components/StatusBadge.vue";
import FieldRow from "@/components/FieldRow.vue";
import TotalRow from "@/components/TotalRow.vue";
import PersonRow from "@/components/PersonRow.vue";
import Score from "@/components/Score.vue";

import { appraisalData } from "@/data/portal";
import { date, dateRange } from "@/utils/format";

const kraCols = [
	{ key: "kra", label: "KRA", primary: true },
	{ key: "weightage", label: "Weight", align: "right", nums: true, muted: true },
	{ key: "completion", label: "Completion", align: "right", nums: true, hideOnMobile: true },
	{ key: "score", label: "Score", align: "right", nums: true },
];

const goalCols = [
	{ key: "kra", label: "Goal", primary: true },
	{ key: "weightage", label: "Weight", align: "right", nums: true, muted: true },
	{ key: "score", label: "Rated", align: "right", nums: true, hideOnMobile: true },
	{ key: "earned", label: "Earned", align: "right", nums: true },
];

const route = useRoute();
const d = computed(() => appraisalData.data);

const tiles = computed(() => [
	{ label: "Final score", value: `${d.value.final_score} / 5` },
	{ label: "Goal score", value: d.value.goal_score ? `${d.value.goal_score} / 5` : "—" },
	{ label: "Self score", value: d.value.self_score ? `${d.value.self_score} / 5` : "—" },
	{
		label: "Feedback",
		value: d.value.feedback_score ? `${d.value.feedback_score} / 5` : "—",
		hint: d.value.feedback.length
			? `${d.value.feedback.length} reviewer${d.value.feedback.length === 1 ? "" : "s"}`
			: "",
	},
]);

watch(
	() => route.params.name,
	(name) => appraisalData.fetch({ name }),
	{ immediate: true },
);
</script>
