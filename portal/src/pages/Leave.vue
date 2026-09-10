<template>
	<PageBody :loading="leaveData.loading && !leaveData.data">
		<PageHead
			title="Leave"
			:subtitle="d?.allocation_period ? `Allocation period ${d.allocation_period}` : ''"
		>
			<template #actions>
				<Button variant="solid" @click="showNew = true">Apply for Leave</Button>
			</template>
		</PageHead>

		<template v-if="d">
			<StatTiles v-if="tiles.length" :tiles="tiles" />

			<DashGrid>
				<template #main>
					<SectionCard title="My Applications" :padded="false">
						<DataTable
							:columns="cols"
							:rows="d.applications"
							clickable
							empty-message="You have not applied for leave yet."
							@row-click="open"
						>
							<template #cell-dates="{ row }">
								{{ dateRange(row.from_date, row.to_date) }}
							</template>
							<template #cell-approver_name="{ row }">
								<span class="text-ink-gray-6">{{ row.approver_name || "—" }}</span>
							</template>
							<template #cell-display_status="{ row }">
								<StatusBadge :status="row.display_status" />
							</template>
						</DataTable>
					</SectionCard>
				</template>

				<template #side>
					<SectionCard title="Balance">
						<BalanceBars :balances="d.balances" />
					</SectionCard>

					<SectionCard title="Team, Next 7 Days">
						<ul v-if="d.team.length" class="flex flex-col gap-2">
							<li
								v-for="t in d.team"
								:key="t.employee + t.from_date"
								class="flex items-center justify-between gap-2"
							>
								<PersonRow
									:name="t.employee_name"
									:to="`/directory/${t.employee}`"
									size="md"
								/>
								<span class="nums shrink-0 text-base text-ink-gray-5">
									{{ dateRange(t.from_date, t.to_date) }}
								</span>
							</li>
						</ul>
						<EmptyState v-else message="Nobody is away in the next week." />
					</SectionCard>
				</template>
			</DashGrid>
		</template>
	</PageBody>

	<RequestDialog v-model:open="showNew" type="leave" @saved="leaveData.fetch()" />
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { Button } from "frappe-ui";

import PageBody from "@/components/PageBody.vue";
import PageHead from "@/components/PageHead.vue";
import DashGrid from "@/components/DashGrid.vue";
import SectionCard from "@/components/SectionCard.vue";
import DataTable from "@/components/DataTable.vue";
import StatTiles from "@/components/StatTiles.vue";
import StatusBadge from "@/components/StatusBadge.vue";
import PersonRow from "@/components/PersonRow.vue";
import BalanceBars from "@/components/BalanceBars.vue";
import EmptyState from "@/components/EmptyState.vue";
import RequestDialog from "@/components/RequestDialog.vue";

import { leaveData } from "@/data/portal";
import { requestPath } from "@/data/requests";
import { dateRange } from "@/utils/format";

const cols = [
	{ key: "leave_type", label: "Type", primary: true },
	{ key: "dates", label: "Dates", nums: true },
	{ key: "total_leave_days", label: "Days", nums: true, hideOnMobile: true },
	{ key: "approver_name", label: "Approver", hideOnMobile: true },
	{ key: "display_status", label: "Status", align: "right", badge: true },
];

const router = useRouter();
const showNew = ref(false);
const d = computed(() => leaveData.data);

const tiles = computed(() =>
	(d.value?.balances || []).slice(0, 4).map((b) => ({
		label: b.leave_type,
		value: b.balance,
		pct: b.pct,
		hint: `of ${b.allocated} allocated`,
	})),
);

function open(row) {
	router.push(requestPath("leave", row.name));
}

onMounted(() => leaveData.fetch());
</script>
