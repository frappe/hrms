<script setup>
import { computed, ref, watch } from "vue";
import { Button, Dropdown, useCall } from "frappe-ui";

import Dashboard from "./Dashboard.vue";
import { getView, PERIODS } from "./dashboard.js";
import { usePageHeadTarget } from "./pageHead.js";

const DASHBOARD =
	"/api/v2/method/hrms.hr.page.recruitment_dashboard.recruitment_dashboard.get_recruitment_dashboard";

const props = defineProps({
	route: { type: Array, default: () => [] },
	query: { type: Object, default: () => ({}) },
});

const __ = window.__;
// the period sits in the URL as ?period=last-90-days, so Back from a list keeps it
const toSlug = (key) => key.replaceAll("_", "-");
const fromSlug = (slug) => PERIODS.find((option) => toSlug(option.key) === slug)?.key;
const period = ref("last_90_days");
watch(
	() => props.query,
	(query) => {
		period.value = fromSlug(query.period) || period.value;
		// desk also copies the query into route_options, which the next list would read as filters
		delete window.frappe?.route_options?.period;
	},
	{ immediate: true },
);
function choosePeriod(key) {
	period.value = key;
	const url = new URL(window.location.href);
	url.searchParams.set("period", toSlug(key));
	history.replaceState(history.state, "", url);
}
// a GET, as desk keeps its CSRF token where frappe-ui does not read it
const call = useCall({
	url: DASHBOARD,
	method: "GET",
	params: () => ({ period: period.value }),
	refetch: true,
});

const loading = computed(() => call.loading);
const error = computed(() => Boolean(call.error) && !call.loading);
const data = computed(() => (loading.value || error.value ? null : call.data));
const view = computed(() => getView(data.value));
const periodLabel = computed(() =>
	__(PERIODS.find((option) => option.key === period.value).label),
);
const periodOptions = computed(() =>
	PERIODS.map((option) => ({
		label: __(option.label),
		key: option.key,
		onClick: () => choosePeriod(option.key),
	})),
);
const canCreateOpening = computed(() =>
	Boolean(window.frappe?.model?.can_create?.("Job Opening")),
);
const newOpening = () => window.frappe?.new_doc?.("Job Opening");
const scroller = ref(null);
const headTarget = usePageHeadTarget(scroller);
</script>

<template>
	<div
		ref="scroller"
		class="h-full overflow-y-auto bg-surface-base text-ink-gray-9 tabular-nums"
	>
		<div class="mx-auto w-full max-w-[1200px] px-3 sm:px-5">
			<div
				v-if="data?.first_use"
				class="mt-5 flex flex-col items-center gap-3 rounded-5 border border-dashed border-outline-gray-2 px-6 py-20 text-center"
			>
				<div
					class="flex size-10 items-center justify-center rounded-4 bg-surface-gray-2 text-ink-gray-5"
				>
					<span class="lucide-briefcase size-5" aria-hidden="true" />
				</div>
				<h2 class="text-base-medium text-ink-gray-8">{{ __("No openings yet") }}</h2>
				<p class="text-p-base text-ink-gray-5">
					{{ __("Hiring numbers appear here once you post a job opening.") }}
				</p>
				<Button
					v-if="canCreateOpening"
					variant="solid"
					theme="gray"
					icon-left="lucide-plus"
					:label="__('New job opening')"
					class="mt-2"
					@click="newOpening"
				/>
			</div>

			<template v-else>
				<Teleport v-if="headTarget" :to="headTarget">
					<Dropdown :options="periodOptions">
						<template #item-suffix="{ item }">
							<span
								v-if="item.key === period"
								class="lucide-check ml-auto size-4 text-ink-gray-7"
								:aria-label="__('Current period')"
							/>
						</template>
						<Button
							:label="periodLabel"
							icon-right="lucide-chevron-down"
							class="whitespace-nowrap"
						/>
					</Dropdown>
				</Teleport>
				<div v-if="error" class="flex items-center gap-2 pt-5">
					<span class="text-p-base text-ink-gray-6">{{
						__("Could not load the dashboard.")
					}}</span>
					<Button size="sm" :label="__('Retry')" @click="call.reload()" />
				</div>
				<Dashboard v-else class="pt-5" :view="view" :loading="loading" />
			</template>
		</div>
	</div>
</template>
