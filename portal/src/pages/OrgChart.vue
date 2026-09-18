<template>
	<PageBody :loading="orgChartData.loading && !orgChartData.data">
		<PageHead title="Org Chart" subtitle="Your reporting line and team" />

		<template v-if="d">
			<SectionCard title="Reporting Structure">
				<!--
					v1 Tree takes a forest (`nodes`) and draws its own elbows via `guides`,
					so the row is composed from the prefix/label slots and there is no
					hand-rolled connector CSS any more.
				-->
				<Tree v-if="treeRoot" :nodes="[treeRoot]" node-key="name" guides="connectors">
					<template #item-prefix="{ node }">
						<Avatar :label="node.label" :image="node.image" size="lg" />
					</template>
					<template #item-label="{ node }">
						<RouterLink
							:to="node.isMe ? '/me' : `/directory/${node.name}`"
							class="flex min-w-0 items-baseline gap-1.5"
							@click.stop
						>
							<span class="shrink-0 text-base text-ink-gray-8">{{
								node.label
							}}</span>
							<span class="shrink-0 font-bold text-ink-gray-4">&middot;</span>
							<span class="truncate text-sm text-ink-gray-5">{{ node.role }}</span>
						</RouterLink>
					</template>
				</Tree>
				<EmptyState v-else message="No reporting structure to show." />
			</SectionCard>
		</template>
	</PageBody>
</template>

<script setup>
import { computed, onMounted } from "vue";
import { Avatar, Tree } from "frappe-ui";

import PageBody from "@/components/PageBody.vue";
import PageHead from "@/components/PageHead.vue";
import SectionCard from "@/components/SectionCard.vue";
import EmptyState from "@/components/EmptyState.vue";

import { orgChartData } from "@/data/portal";

const d = computed(() => orgChartData.data);

function toNode(person, extra = {}) {
	return {
		name: person.name,
		label: person.employee_name,
		role: person.designation || "—",
		image: person.image,
		children: [],
		...extra,
	};
}

/** skip-level → manager → peers (with you expanded into your reports). */
const treeRoot = computed(() => {
	const data = d.value;
	if (!data?.me) return null;

	const me = toNode(data.me, {
		isMe: true,
		children: (data.reports || []).map((r) => toNode(r)),
	});

	const siblings = data.peers?.length
		? data.peers.map((p) => (p.name === data.me.name ? me : toNode(p)))
		: [me];

	if (!data.manager) return me;

	const manager = toNode(data.manager, { children: siblings });
	return data.skip ? toNode(data.skip, { children: [manager] }) : manager;
});

onMounted(() => orgChartData.fetch());
</script>
