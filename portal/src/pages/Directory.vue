<template>
	<PageBody :loading="directoryData.loading && !directoryData.data">
		<PageHead title="Directory" :subtitle="`${filtered.length} of ${d?.total || 0} people`">
			<template #actions>
				<Button variant="subtle" @click="$router.push('/org-chart')"
					>Open Org Chart</Button
				>
			</template>
		</PageHead>

		<div class="flex flex-col gap-3">
			<FormControl
				v-model="search"
				type="text"
				placeholder="Search by name or role"
				autocomplete="off"
			/>

			<!--
				TabButtons rather than Tabs: these pick a filter, so the semantics are
				a radiogroup, not a tablist. Desktop keeps them visible rather than
				hiding them behind a sheet; the row scrolls when the list is long.
			-->
			<div class="scroll-x pb-1">
				<TabButtons v-model="active" :buttons="facets" />
			</div>
		</div>

		<div v-if="filtered.length" class="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
			<RouterLink
				v-for="p in filtered"
				:key="p.name"
				:to="`/directory/${p.name}`"
				class="flex items-center gap-3 rounded-lg border border-outline-gray-1 bg-surface-white p-3 transition-colors hover:bg-surface-gray-1"
			>
				<Avatar :label="p.employee_name" :image="p.image" size="3xl" />
				<div class="min-w-0 flex-1">
					<div class="truncate text-base font-semibold text-ink-gray-9">
						{{ p.employee_name }}
					</div>
					<div class="truncate text-sm text-ink-gray-5">
						{{ p.designation || "—" }}
					</div>
				</div>
				<StatusBadge
					class="shrink-0"
					:status="p.is_self ? 'you' : p.availability"
					:label="p.is_self ? 'You' : p.availability"
				/>
			</RouterLink>
		</div>
		<SectionCard v-else>
			<EmptyState message="Nobody matches that search." />
		</SectionCard>
	</PageBody>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { Avatar, Button, FormControl, TabButtons } from "frappe-ui";

import PageBody from "@/components/PageBody.vue";
import PageHead from "@/components/PageHead.vue";
import SectionCard from "@/components/SectionCard.vue";
import StatusBadge from "@/components/StatusBadge.vue";
import EmptyState from "@/components/EmptyState.vue";

import { directoryData } from "@/data/portal";

const search = ref("");
const active = ref("all");

const d = computed(() => directoryData.data);

const facets = computed(() => {
	const out = [
		{ value: "all", label: "All" },
		{ value: "available", label: "Available today" },
	];
	for (const dept of d.value?.departments || []) {
		out.push({ value: `dept:${dept}`, label: dept });
	}
	for (const b of d.value?.branches || []) {
		out.push({ value: `branch:${b}`, label: b });
	}
	return out;
});

const filtered = computed(() => {
	let list = d.value?.people || [];
	const q = search.value.trim().toLowerCase();
	if (q) {
		list = list.filter(
			(p) =>
				p.employee_name?.toLowerCase().includes(q) ||
				p.designation?.toLowerCase().includes(q) ||
				p.department?.toLowerCase().includes(q),
		);
	}
	const a = active.value;
	if (a === "available") list = list.filter((p) => p.availability === "Available");
	else if (a.startsWith("dept:")) list = list.filter((p) => p.department === a.slice(5));
	else if (a.startsWith("branch:")) list = list.filter((p) => p.branch === a.slice(7));
	return list;
});

onMounted(() => directoryData.fetch());
</script>
