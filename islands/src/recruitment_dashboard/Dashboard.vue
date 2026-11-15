<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { BarChart, ChartCard, DonutChart, NumberCard } from "frappe-ui/charts";
import { useHost } from "@framework/ui/island";

import ChartHeading from "./ChartHeading.vue";
import ChartKey from "./ChartKey.vue";
import DonutCentre from "./DonutCentre.vue";
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
const showKey = computed(() => !props.loading && !props.view.empty);

const categorical = (count) =>
	Array.from({ length: count }, (_, index) => `var(--chart-categorical-${index + 1})`);
// stage colours are set per theme in the style block: the dark ramp's deep end is too faint
const stage = (step) => `var(--recruitment-stage-${step})`;
// frappe-ui sizes the label column but shortens in the middle; keep the start, cut the end
const rowLabels = {
	animation: false,
	yAxis: { axisLabel: { formatter: (label) => label, overflow: "truncate", ellipsis: "…" } },
};

const openingsPlot = ref(null);
const openingsWidth = ref(0);
// both donut keys take the taller one's height, so the two rings get the same room
const donutKeyHeights = ref(new Map());
const donutKeyHeight = computed(() => Math.max(0, ...donutKeyHeights.value.values()));
const resizeObserver = new ResizeObserver((entries) => {
	const heights = new Map(donutKeyHeights.value);
	for (const { target, contentRect } of entries) {
		if (target === openingsPlot.value) openingsWidth.value = contentRect.width;
		else if (target.isConnected) heights.set(target, target.offsetHeight);
		else {
			heights.delete(target);
			resizeObserver.unobserve(target);
		}
	}
	donutKeyHeights.value = heights;
});
onMounted(() => resizeObserver.observe(openingsPlot.value));
onBeforeUnmount(() => resizeObserver.disconnect());
const observeDonutKey = (component) => component && resizeObserver.observe(component.$el);

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

const stageNames = STAGES.map((stage) => __(stage));
const stageColors = [1, 2, 3, 4, 5].map(stage);
const stageKey = stageNames.map((label, index) => ({ label, color: stageColors[index] }));
const outcomeNames = OUTCOMES.map((outcome) => __(outcome));
const sourceStageColors = [stage(1), "var(--recruitment-interviewed)", stage(5)];
const sourceStageKey = outcomeNames.map((label, index) => ({
	label,
	color: sourceStageColors[index],
}));
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
const sourceColors = computed(() => categorical(props.view.sourceNames.length));
const sourceKey = computed(() =>
	props.view.sourceNames.map((label, index) => ({ label, color: sourceColors.value[index] })),
);

const keyFor = (rows) =>
	rows.map((row, index) => ({
		label: row.name,
		color: `var(--chart-categorical-${index + 1})`,
		count: row.count,
	}));
const colorsFor = (key) => Object.fromEntries(key.map((item) => [item.label, item.color]));
const offersKey = computed(() => keyFor(props.view.offers));
const interviewsKey = computed(() => keyFor(props.view.interviews));
const still = { animation: false };

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
const stageOf = (label) => STAGES[stageNames.indexOf(label)];
const outcomeKey = (label) => OUTCOMES[outcomeNames.indexOf(label)];
const funnelTarget = (stage) => targets.value?.funnel(stage) ?? null;
// series whose marks open nothing keep the default cursor
const stillCursor = (names) =>
	Object.fromEntries(names.map((name) => [name, { echartOptions: { cursor: "default" } }]));
const weekSeries = computed(() =>
	stillCursor(
		props.view.sourceNames.filter((name) => !targets.value?.week({ from: "", to: "" }, name)),
	),
);
const outcomeSeries = stillCursor(outcomeNames.filter((label) => outcomeKey(label) !== "Hired"));
</script>

<template>
	<!-- svg labels must not inherit desk's letter-spacing: echarts measures them without it -->
	<div
		class="space-y-4 pb-10 stage-colors [&_[data-slot=chart-legend]]:hidden [&_[data-slot=chart-plot]_svg]:tracking-normal"
	>
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
				<div ref="openingsPlot" class="min-h-0 flex-1">
					<BarChart
						:data="view.chartRows"
						x="role"
						:y="stageNames"
						horizontal
						stacked
						:palette="stageColors"
						:echart-options="openingLabels"
						:loading="loading"
						@select="open((t) => t.opening($event.row, stageOf($event.name)))"
					>
						<template #tooltip="tooltip">
							<StackTooltip v-bind="tooltip" :order="stageNames" />
						</template>
					</BarChart>
				</div>
				<ChartKey v-if="showKey" :items="stageKey" />
			</div>
		</ChartCard>

		<!-- side by side only from 1280: narrower, the funnel cuts its stage names and the donuts shrink -->
		<div class="grid grid-cols-1 gap-4 xl:grid-cols-12">
			<ChartCard class="h-[320px] xl:col-span-5">
				<div class="flex h-full flex-col gap-1.5">
					<ChartHeading :title="__('Applications per week')" />
					<div class="min-h-0 flex-1">
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
					<ChartKey v-if="showKey" :items="sourceKey" />
				</div>
			</ChartCard>
			<FunnelCard
				class="xl:col-span-7"
				:funnel="view.funnel"
				:caption="view.funnelCaption"
				:colors="stageColors"
				:show-caption="showKey"
				:loading="loading"
				:target="funnelTarget"
				@open="openList"
			/>
		</div>

		<div class="grid grid-cols-1 gap-4 xl:grid-cols-12">
			<ChartCard class="h-[320px] xl:col-span-6 xl:h-[360px]">
				<div class="flex h-full flex-col gap-1.5">
					<ChartHeading :title="__('Hires by source')" />
					<div class="min-h-0 flex-1">
						<BarChart
							:data="view.sources"
							x="source"
							:y="outcomeNames"
							horizontal
							stacked
							:palette="sourceStageColors"
							:echart-options="rowLabels"
							:series-config="outcomeSeries"
							:loading="loading"
							@select="
								open((t) => t.hiresBySource($event.row, outcomeKey($event.name)))
							"
						>
							<template #tooltip="tooltip">
								<StackTooltip v-bind="tooltip" :order="outcomeNames" />
							</template>
						</BarChart>
					</div>
					<ChartKey v-if="showKey" :items="sourceStageKey" />
				</div>
			</ChartCard>
			<!-- side by side only from 1024; at 1280 the row is taller, as each ring sits over three key rows and its centre label must fit. Both reserve two subtitle lines and the taller key, so their rings match -->
			<div class="grid grid-cols-1 gap-4 lg:grid-cols-2 xl:col-span-6">
				<ChartCard class="h-[320px] xl:h-[360px]">
					<div class="flex h-full flex-col gap-1.5">
						<ChartHeading
							class="min-h-[60px]"
							:title="__('Offers made')"
							:subtitle="view.offersSubtitle"
						/>
						<div class="min-h-0 flex-1">
							<DonutChart
								:data="view.offers"
								category="name"
								value="count"
								order="rows"
								:center-label="__('offers')"
								:colors="colorsFor(offersKey)"
								:echart-options="still"
								:loading="loading"
								@select="open((t) => t.offer($event.rows[0].status))"
							>
								<template #center="center">
									<DonutCentre v-bind="center" />
								</template>
							</DonutChart>
						</div>
						<div :style="{ minHeight: `${donutKeyHeight}px` }">
							<ChartKey
								v-if="showKey && view.offers.length"
								:ref="observeDonutKey"
								:items="offersKey"
							/>
						</div>
					</div>
				</ChartCard>
				<ChartCard class="h-[320px] xl:h-[360px]">
					<div class="flex h-full flex-col gap-1.5">
						<ChartHeading
							class="min-h-[60px]"
							:title="__('Interviews held')"
							:subtitle="view.interviewsSubtitle"
						/>
						<div class="min-h-0 flex-1">
							<DonutChart
								:data="view.interviews"
								category="name"
								value="count"
								order="rows"
								:center-label="__('interviews')"
								:colors="colorsFor(interviewsKey)"
								:echart-options="still"
								:loading="loading"
								@select="open((t) => t.interview($event.rows[0].status))"
							>
								<template #center="center">
									<DonutCentre v-bind="center" />
								</template>
							</DonutChart>
						</div>
						<div :style="{ minHeight: `${donutKeyHeight}px` }">
							<ChartKey
								v-if="showKey && view.interviews.length"
								:ref="observeDonutKey"
								:items="interviewsKey"
							/>
						</div>
					</div>
				</ChartCard>
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
