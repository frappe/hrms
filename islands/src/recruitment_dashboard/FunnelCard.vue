<script setup>
import { computed, onBeforeUnmount, ref } from "vue";
import { BarChart, ChartCard, FunnelChart } from "frappe-ui/charts";

import ChartHeading from "./ChartHeading.vue";

const props = defineProps({
	// rows of { stage, key, count }, stage translated and key the STAGES name
	funnel: { type: Array, required: true },
	caption: { type: String, default: undefined },
	colors: { type: Array, required: true },
	showCaption: { type: Boolean, default: false },
	loading: { type: Boolean, default: false },
	// the list a stage opens, by STAGES name, or null
	target: { type: Function, default: () => null },
});
const emit = defineEmits(["open"]);

const __ = window.__;
// below 1024 the funnel's five columns cut their stage names, so it reads as bars
const wide = window.matchMedia("(min-width: 1024px)");
const isWide = ref(wide.matches);
const onWidth = (event) => (isWide.value = event.matches);
wide.addEventListener("change", onWidth);
onBeforeUnmount(() => wide.removeEventListener("change", onWidth));

const stageOf = (label) => props.funnel.find((row) => row.stage === label);
const open = (label) => {
	const target = props.target(stageOf(label)?.key);
	if (target) emit("open", target);
};

// as FunnelChart prints a share of the first stage
const share = (value) => {
	const first = props.funnel[0]?.count;
	if (!first || !value) return "0%";
	const percent = (value / first) * 100;
	return percent < 1 ? "<1%" : `${Math.round(percent)}%`;
};
// one series per stage, each row holding only its own, so every bar takes its stage colour
const bars = computed(() =>
	props.funnel.map((row) => ({ stage: row.stage, [row.stage]: row.count })),
);
const stageNames = computed(() => props.funnel.map((row) => row.stage));
const barSeries = computed(() =>
	Object.fromEntries(
		props.funnel.map((row, index) => [
			row.stage,
			{
				format: (value) => (index ? `${value} · ${share(value)}` : String(value)),
				showDataLabels: true,
				// the bars share one slot instead of sitting side by side
				echartOptions: {
					barGap: "-100%",
					cursor: props.target(row.key) ? "pointer" : "default",
				},
			},
		]),
	),
);
const barOptions = {
	animation: false,
	yAxis: { axisLabel: { formatter: (label) => label } },
	grid: { right: 72 },
};
</script>

<template>
	<ChartCard class="h-[320px]">
		<div class="flex h-full flex-col">
			<div class="min-h-0 flex-1 tracking-normal">
				<FunnelChart
					v-if="isWide"
					:title="__('Funnel')"
					:data="funnel"
					category="stage"
					value="count"
					:palette="colors"
					:loading="loading"
					@select="open($event.label)"
				/>
				<div v-else class="flex h-full flex-col gap-1.5">
					<ChartHeading :title="__('Funnel')" />
					<div class="min-h-0 flex-1">
						<BarChart
							:data="bars"
							x="stage"
							:y="stageNames"
							horizontal
							:palette="colors"
							:series-config="barSeries"
							:echart-options="barOptions"
							:loading="loading"
							@select="open($event.row.stage)"
						/>
					</div>
				</div>
			</div>
			<p v-if="showCaption" class="pt-2 text-p-base text-ink-gray-6">
				{{ caption }}
			</p>
		</div>
	</ChartCard>
</template>
