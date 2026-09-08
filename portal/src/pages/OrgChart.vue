<template>
	<PageBody :loading="orgChartData.loading && !orgChartData.data">
		<PageHead title="Org Chart" subtitle="Your reporting line and team" />

		<template v-if="d">
			<SectionCard title="Reporting Structure">
				<!--
					frappe-ui Tree. The published 0.1.278 takes a single `node` root with
					node/icon/label slots, rather than the `nodes` array and item-* slots
					the docs describe, so the avatar row is built in the label slot.
				-->
				<div v-if="treeRoot" class="org-tree">
					<Tree :node="treeRoot" node-key="name" :options="treeOptions">
						<template #label="{ node }">
							<RouterLink
								:to="node.isMe ? '/me' : `/directory/${node.name}`"
								class="-ml-1 flex min-w-0 items-center gap-2.5 rounded-md px-2 py-1.5 transition-colors hover:bg-surface-gray-2"
								:class="node.isMe && 'bg-surface-gray-3'"
								@click.stop
							>
								<Avatar :label="node.label" :image="node.image" size="xl" />
								<div class="flex min-w-0 items-baseline gap-1.5">
									<span class="shrink-0 text-base text-ink-gray-8">{{
										node.label
									}}</span>
									<span class="shrink-0 font-bold text-ink-gray-4"
										>&middot;</span
									>
									<span class="truncate text-sm text-ink-gray-5">{{
										node.role
									}}</span>
								</div>
							</RouterLink>
						</template>
					</Tree>
				</div>
				<EmptyState v-else message="No reporting structure to show." />
			</SectionCard>

			<SectionCard title="Headcount">
				<dl class="flex flex-col">
					<FieldRow
						v-for="dept in d.departments"
						:key="dept.name"
						:label="dept.name"
						:value="`${dept.count} ${dept.count === 1 ? 'person' : 'people'}`"
						nums
					/>
				</dl>
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
import FieldRow from "@/components/FieldRow.vue";
import EmptyState from "@/components/EmptyState.vue";

import { orgChartData } from "@/data/portal";

const d = computed(() => orgChartData.data);

const treeOptions = {
	rowHeight: "48px",
	indentWidth: "28px",
	// elbows are drawn in CSS below; the built-in guide is a plain vertical rule
	showIndentationGuides: false,
	defaultCollapsed: false,
};

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

<style scoped>
/*
	The published Tree only offers a plain vertical rule. These rules draw the
	`guides="connectors"` elbows the docs describe: a vertical run down each
	sibling group, stopping at the last child, with a stub into every row.
*/
.org-tree :deep(li) {
	position: relative;
}

.org-tree :deep(li)::before,
.org-tree :deep(li)::after {
	content: "";
	position: absolute;
	border-color: var(--outline-gray-2);
}

/* vertical run, trimmed to the elbow on the last sibling */
.org-tree :deep(li)::before {
	left: -14px;
	top: 0;
	height: 100%;
	border-left-width: 1px;
}

.org-tree :deep(li:last-child)::before {
	height: 24px;
}

/* horizontal stub into the row, at the row's vertical centre */
.org-tree :deep(li)::after {
	left: -14px;
	top: 24px;
	width: 14px;
	border-top-width: 1px;
}
</style>
