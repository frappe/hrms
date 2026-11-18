<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { BarChart, ChartCard, NumberCard } from "frappe-ui/charts";
import { useHost } from "@framework/ui/island";

import ChartHeading from "./ChartHeading.vue";
import DonutCard from "./DonutCard.vue";
import FunnelCard from "./FunnelCard.vue";
import StackTooltip from "./StackTooltip.vue";
import { OUTCOMES, STAGES } from "./dashboard.js";
import { getListRoute } from "./drilldown.js";

const props = defineProps({
	view: { type: Object, required: true },
	loading: { type: Boolean, default: false },
});

const __ = window.__;
const host = useHost();
// stage colours are set per theme in the style block: the dark ramp's deep end is too faint
const stage = (step) => `var(--recruitment-stage-${step})`;
// frappe-ui sizes the label column but shortens in the middle; keep the start, cut the end
const rowLabels = {
	animation: false,
	yAxis: { axisLabel: { formatter: (label) => label, overflow: "truncate", ellipsis: "…" } },
};

const openingsPlot = ref(null);
const openingsWidth = ref(0);
const resizeObserver = new ResizeObserver(
	([entry]) => (openingsWidth.value = entry.contentRect.width),
);
onMounted(() => resizeObserver.observe(openingsPlot.value));
onBeforeUnmount(() => resizeObserver.disconnect());

// openings sharing a title end in "(location)": shorten the title so that part stays
const openingLabels = computed(() => {
	// frappe-ui's own column rule (a third of the plot, at least 56px), set here so we know it
	const width = Math.max(56, Math.round(openingsWidth.value * 0.32));
	return {
		animation: false,
		yAxis: {
			axisLabel: {
				width,
				overflow: "truncate",
				ellipsis: "…",
				formatter: (label) => fitOpeningLabel(label, width - 8),
			},
		},
	};
});

let labelContext;
function measureLabel(text) {
	labelContext ??= document.createElement("canvas").getContext("2d");
	labelContext.font = "11px InterVar, Inter, sans-serif";
	return labelContext.measureText(text).width;
}

function fitOpeningLabel(label, width) {
	const match = label.match(/^(.+) (\(.+\))$/);
	if (!match || measureLabel(label) <= width) return label;
	const [, title, place] = match;
	let length = title.length;
	const shortened = () => `${title.slice(0, length).trimEnd()}… ${place}`;
	while (length > 1 && measureLabel(shortened()) > width) length--;
	return shortened();
}

// flat week labels, every other one (sparser on long periods), as in the design
const weekLabels = computed(() => {
	const step = Math.max(2, Math.ceil(props.view.weeklySources.length / 7));
	return {
		animation: false,
		grid: { bottom: 24 },
		xAxis: {
			axisLabel: {
				rotate: 0,
				// pinning the last label would crowd its neighbour unless it falls on the step
				showMaxLabel: (props.view.weeklySources.length - 1) % step === 0,
				interval: (index) => index % step === 0,
			},
		},
	};
});

// series keep their untranslated names, so a selected mark names its stage or outcome
const labelled = (keys) => Object.fromEntries(keys.map((key) => [key, { label: __(key) }]));
// a series that opens no list keeps the default cursor
const still = { echartOptions: { cursor: "default" } };
const stageSeries = labelled(STAGES);
const stageColors = [1, 2, 3, 4, 5].map(stage);
const outcomeSeries = Object.fromEntries(
	OUTCOMES.map((outcome) => [
		outcome,
		{ label: __(outcome), ...(outcome === "Hired" ? {} : still) },
	]),
);
const sourceStageColors = [stage(1), "var(--recruitment-interviewed)", stage(5)];
const sourceColors = computed(() =>
	props.view.sourceNames.map((_, index) => `var(--chart-categorical-${index + 1})`),
);
const applicationsChange = computed(() => {
	const delta = props.view.applicationsDelta;
	if (delta == null) return null;
	if (delta === 0) return { percent: "0%", tone: "text-ink-gray-6" };
	return {
		percent: `${Math.abs(delta)}%`,
		tone: delta > 0 ? "text-ink-green-7" : "text-ink-red-7",
		icon: delta > 0 ? "lucide-arrow-up-right" : "lucide-arrow-down-left",
	};
});

const targets = computed(() => props.view.targets);
const openList = (target) => target && host.navigate(getListRoute(target));
// a card that opens its list: a link for the keyboard too
const linkCard = (name) =>
	targets.value
		? {
				role: "link",
				tabindex: 0,
				class: "cursor-pointer hover:border-outline-gray-3 focus-visible:focus-ring",
				onClick: () => openList(targets.value[name]),
				onKeydown: (event) => event.key === "Enter" && openList(targets.value[name]),
		  }
		: {};
const open = (pick) => targets.value && openList(pick(targets.value));
const funnelTarget = (stage) => targets.value?.funnel(stage) ?? null;
const weekSeries = computed(() =>
	Object.fromEntries(
		props.view.sourceNames
			.filter((name) => !targets.value?.hasSource(name))
			.map((name) => [name, still]),
	),
);
</script>

<template>
	<!-- plots take tracking-normal: echarts measures its svg labels without desk's letter-spacing -->
	<div class="space-y-4 pb-10 stage-colors">
		<!-- five across from 1280, three and two from 1024, two a row below, so no caption is cut -->
		<div class="grid grid-cols-2 gap-4 lg:grid-cols-6 xl:grid-cols-5">
			<NumberCard
				class="min-h-[124px] lg:col-span-2 xl:col-span-1"
				v-bind="linkCard('openRoles')"
				:title="__('Open roles')"
				:value="view.openRoles"
				:loading="loading"
			>
				<template #caption>
					<span class="min-w-0 text-ink-gray-5">{{ view.positionsCaption }}</span>
				</template>
			</NumberCard>
			<NumberCard
				class="min-h-[124px] lg:col-span-2 xl:col-span-1"
				v-bind="linkCard('hired')"
				:title="__('Hired')"
				:value="view.hired"
				:progress="
					view.hiredPercent == null
						? undefined
						: { value: view.hiredPercent, color: stage(5) }
				"
				:loading="loading"
			>
				<template #caption>
					<span class="min-w-0 text-ink-gray-5">{{ view.hiredCaption }}</span>
				</template>
			</NumberCard>
			<NumberCard
				class="min-h-[124px] lg:col-span-2 xl:col-span-1"
				v-bind="linkCard('applications')"
				:title="__('Applications')"
				:value="view.applications"
				:loading="loading"
			>
				<!-- the change as NumberCard draws its delta, but the comparison can drop to its own line -->
				<template #caption>
					<span class="flex min-w-0 flex-wrap items-center gap-x-1">
						<span
							v-if="applicationsChange"
							class="inline-flex items-center gap-1 whitespace-nowrap text-sm-medium tabular-nums"
							:class="applicationsChange.tone"
						>
							<span
								v-if="applicationsChange.icon"
								class="size-4 shrink-0"
								:class="applicationsChange.icon"
								aria-hidden="true"
							/>
							{{ applicationsChange.percent }}
						</span>
						<span class="text-ink-gray-5">{{ view.applicationsCaption }}</span>
					</span>
				</template>
			</NumberCard>
			<NumberCard
				class="min-h-[124px] lg:col-span-3 xl:col-span-1"
				:title="__('Time to hire')"
				:value="view.timeToHire"
				:suffix="` ${__('days')}`"
				:loading="loading"
			>
				<template #caption>
					<span class="min-w-0 text-ink-gray-5">{{ view.timeToHireCaption }}</span>
				</template>
			</NumberCard>
			<NumberCard
				class="col-span-2 min-h-[124px] lg:col-span-3 xl:col-span-1"
				v-bind="linkCard('notReviewed')"
				:title="__('Not reviewed')"
				:value="view.notReviewed"
				:loading="loading"
			>
				<template #caption>
					<span class="min-w-0 text-ink-gray-5">{{ view.notReviewedCaption }}</span>
				</template>
			</NumberCard>
		</div>

		<ChartCard class="h-[320px]">
			<div class="flex h-full flex-col gap-1.5">
				<ChartHeading :title="view.chartTitle" :subtitle="view.attention" />
				<div ref="openingsPlot" class="min-h-0 flex-1 tracking-normal">
					<BarChart
						:data="view.chartRows"
						x="role"
						:y="STAGES"
						horizontal
						stacked
						:palette="stageColors"
						:series-config="stageSeries"
						:echart-options="openingLabels"
						:loading="loading"
						@select="open((t) => t.opening($event.row, $event.name))"
					>
						<template #tooltip="tooltip">
							<StackTooltip v-bind="tooltip" :order="STAGES" />
						</template>
					</BarChart>
				</div>
			</div>
		</ChartCard>

		<!-- side by side only from 1280: narrower, the funnel cuts its stage names and the donuts shrink -->
		<div class="grid grid-cols-1 gap-4 xl:grid-cols-12">
			<ChartCard class="h-[320px] xl:col-span-5">
				<div class="flex h-full flex-col gap-1.5">
					<ChartHeading :title="__('Applications per week')" />
					<div class="min-h-0 flex-1 tracking-normal">
						<BarChart
							:data="view.weeklySources"
							x="week"
							:y="view.sourceNames"
							stacked
							:palette="sourceColors"
							:echart-options="weekLabels"
							:series-config="weekSeries"
							:y-axis="{ integer: true }"
							:loading="loading"
							@select="open((t) => t.week($event.row, $event.name))"
						>
							<template #tooltip="tooltip">
								<StackTooltip v-bind="tooltip" :order="view.sourceNames" />
							</template>
						</BarChart>
					</div>
				</div>
			</ChartCard>
			<FunnelCard
				class="xl:col-span-7"
				:funnel="view.funnel"
				:caption="view.funnelCaption"
				:colors="stageColors"
				:show-caption="!loading && !view.empty"
				:loading="loading"
				:target="funnelTarget"
				@open="openList"
			/>
		</div>

		<div class="grid grid-cols-1 gap-4 xl:grid-cols-12">
			<ChartCard class="h-[320px] xl:col-span-6 xl:h-[360px]">
				<div class="flex h-full flex-col gap-1.5">
					<ChartHeading :title="__('Hires by source')" />
					<div class="min-h-0 flex-1 tracking-normal">
						<BarChart
							:data="view.sources"
							x="source"
							:y="OUTCOMES"
							horizontal
							stacked
							:palette="sourceStageColors"
							:echart-options="rowLabels"
							:series-config="outcomeSeries"
							:loading="loading"
							@select="open((t) => t.hiresBySource($event.row, $event.name))"
						>
							<template #tooltip="tooltip">
								<StackTooltip v-bind="tooltip" :order="OUTCOMES" />
							</template>
						</BarChart>
					</div>
				</div>
			</ChartCard>
			<!-- side by side only from 1024; at 1280 the row is taller, as each ring sits over its legend and its centre label must fit -->
			<div class="grid grid-cols-1 gap-4 lg:grid-cols-2 xl:col-span-6">
				<DonutCard
					:title="__('Offers made')"
					:subtitle="view.offersSubtitle"
					:slices="view.offers"
					:center-label="__('offers')"
					:loading="loading"
					@open="open((t) => t.offer($event))"
				/>
				<DonutCard
					:title="__('Interviews held')"
					:subtitle="view.interviewsSubtitle"
					:slices="view.interviews"
					:center-label="__('interviews')"
					:loading="loading"
					@open="open((t) => t.interview($event))"
				/>
			</div>
		</div>
	</div>
</template>

<style scoped>
/* light keeps the frappe-ui ramp; dark is the same hue lifted to at least 3:1 on the card */
.stage-colors {
	--recruitment-stage-1: var(--chart-sequential-7);
	--recruitment-stage-2: var(--chart-sequential-5);
	--recruitment-stage-3: var(--chart-sequential-4);
	--recruitment-stage-4: var(--chart-sequential-2);
	--recruitment-stage-5: var(--chart-sequential-1);
	--recruitment-interviewed: var(--chart-sequential-3);
}
[data-theme="dark"] .stage-colors {
	--recruitment-stage-1: #b9d9ed;
	--recruitment-stage-2: #8bbfdf;
	--recruitment-stage-3: #5fa6d1;
	--recruitment-stage-4: #3990c5;
	--recruitment-stage-5: #137ab9;
	--recruitment-interviewed: #5fa6d1;
}
</style>
