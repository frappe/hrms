<template>
	<PageBody :loading="expensesData.loading && !expensesData.data">
		<PageHead title="Expenses" subtitle="Your claims and reimbursements">
			<template #actions>
				<Button variant="solid" @click="showNew = true">New Claim</Button>
			</template>
		</PageHead>

		<template v-if="d">
			<StatTiles :tiles="tiles" />

			<DashGrid>
				<template #main>
					<SectionCard title="My Claims" :padded="false">
						<DataTable
							:columns="cols"
							:rows="d.claims"
							clickable
							empty-message="You have not claimed any expenses yet."
							@row-click="open"
						>
							<template #cell-total_claimed_amount="{ row }">
								{{ money(row.total_claimed_amount, { currency: row.currency }) }}
							</template>
							<template #cell-posting_date="{ row }">
								{{ row.posting_date ? date(row.posting_date) : "Not submitted" }}
							</template>
							<template #cell-display_status="{ row }">
								<StatusBadge :status="row.display_status" />
							</template>
						</DataTable>
					</SectionCard>
				</template>

				<template #side>
					<SectionCard title="Claim Types" readonly-label="As per policy">
						<dl v-if="d.claim_types.length" class="flex flex-col">
							<FieldRow
								v-for="t in d.claim_types"
								:key="t.name"
								:label="t.name"
								:value="t.description || 'No description'"
								locked
							/>
						</dl>
						<EmptyState v-else message="No expense claim types configured." />
					</SectionCard>
				</template>
			</DashGrid>
		</template>
	</PageBody>

	<RequestDialog
		v-model:open="showNew"
		type="expense"
		:currency="d?.claim_currency"
		@saved="expensesData.fetch()"
	/>
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
import FieldRow from "@/components/FieldRow.vue";
import EmptyState from "@/components/EmptyState.vue";
import RequestDialog from "@/components/RequestDialog.vue";

import { expensesData } from "@/data/portal";
import { requestPath } from "@/data/requests";
import { date, money } from "@/utils/format";

const cols = [
	{ key: "name", label: "Claim", nums: true, hideOnMobile: true },
	{ key: "purpose", label: "Purpose", primary: true },
	{ key: "posting_date", label: "Submitted", nums: true, muted: true },
	{ key: "total_claimed_amount", label: "Amount", align: "right", nums: true },
	{ key: "display_status", label: "Status", align: "right", badge: true },
];

const router = useRouter();
const d = computed(() => expensesData.data);
const showNew = ref(false);

const tiles = computed(() => {
	const s = d.value?.stats || {};
	return [
		{
			label: "Claimed",
			value: money(s.claimed, { compact: true }),
			hint: `${s.count || 0} claims`,
		},
		{
			label: "Awaiting Approval",
			value: money(s.awaiting, { compact: true }),
			hint:
				s.oldest_age !== null && s.oldest_age !== undefined
					? `oldest ${s.oldest_age} days`
					: "nothing pending",
		},
		{ label: "Reimbursed", value: money(s.reimbursed, { compact: true }), hint: "paid out" },
	];
});

function open(row) {
	router.push(requestPath("expense", row.name));
}

onMounted(() => expensesData.fetch());
</script>
