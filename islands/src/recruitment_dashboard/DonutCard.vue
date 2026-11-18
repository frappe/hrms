<script setup>
import { computed } from "vue";
import { ChartCard, DonutChart } from "frappe-ui/charts";

import ChartHeading from "./ChartHeading.vue";
import DonutCentre from "./DonutCentre.vue";

const props = defineProps({
	title: { type: String, required: true },
	subtitle: { type: String, default: undefined },
	// rows of { name, status, count }, name translated
	slices: { type: Array, required: true },
	centerLabel: { type: String, required: true },
	loading: { type: Boolean, default: false },
});
const emit = defineEmits(["open"]);
const still = { animation: false };
// each slice keeps the categorical colour of its row, so a status always has the same colour
const colors = computed(() =>
	Object.fromEntries(
		props.slices.map((slice, index) => [slice.name, `var(--chart-categorical-${index + 1})`]),
	),
);
</script>

<!-- the heading reserves two subtitle lines, so side by side both rings get the same room -->
<template>
	<ChartCard class="h-[320px] xl:h-[360px]">
		<div class="flex h-full flex-col gap-1.5">
			<ChartHeading class="min-h-[60px]" :title="title" :subtitle="subtitle" />
			<div class="min-h-0 flex-1 tracking-normal">
				<DonutChart
					:data="slices"
					category="name"
					value="count"
					order="rows"
					:center-label="centerLabel"
					:colors="colors"
					:echart-options="still"
					:loading="loading"
					@select="emit('open', $event.rows[0].status)"
				>
					<template #center="center">
						<DonutCentre v-bind="center" />
					</template>
				</DonutChart>
			</div>
		</div>
	</ChartCard>
</template>
