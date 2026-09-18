<template>
	<PageBody :loading="advancesData.loading && !advancesData.data">
		<PageHead title="Advances" subtitle="Salary and travel advances">
			<template #actions>
				<Button variant="solid" @click="showNew = true">Request Advance</Button>
			</template>
		</PageHead>

		<template v-if="d">
			<StatTiles :tiles="tiles" />

			<SectionCard title="My Advances" :padded="false">
				<DataTable
					:columns="cols"
					:rows="d.advances"
					clickable
					empty-message="You have not requested an advance."
					@row-click="open"
				>
					<template #cell-posting_date="{ row }">{{ date(row.posting_date) }}</template>
					<template #cell-advance_amount="{ row }">
						{{ money(row.advance_amount) }}
					</template>
					<template #cell-outstanding="{ row }">
						{{ money(outstanding(row)) }}
					</template>
					<template #cell-status="{ row }">
						<StatusBadge :status="row.docstatus === 0 ? 'Draft' : row.status" />
					</template>
				</DataTable>
			</SectionCard>
		</template>
	</PageBody>

	<RequestDialog v-model:open="showNew" type="advance" @saved="advancesData.fetch()" />
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { Button } from "frappe-ui";

import PageBody from "@/components/PageBody.vue";
import PageHead from "@/components/PageHead.vue";
import SectionCard from "@/components/SectionCard.vue";
import DataTable from "@/components/DataTable.vue";
import StatTiles from "@/components/StatTiles.vue";
import StatusBadge from "@/components/StatusBadge.vue";
import RequestDialog from "@/components/RequestDialog.vue";

import { advancesData } from "@/data/portal";
import { requestPath } from "@/data/requests";
import { date, money } from "@/utils/format";

const cols = [
	{ key: "name", label: "Reference", nums: true, hideOnMobile: true },
	{ key: "purpose", label: "Purpose", primary: true },
	{ key: "posting_date", label: "Requested", nums: true, muted: true },
	{ key: "advance_amount", label: "Amount", align: "right", nums: true },
	{ key: "outstanding", label: "Outstanding", align: "right", nums: true, hideOnMobile: true },
	{ key: "status", label: "Status", align: "right", badge: true },
];

const router = useRouter();
const showNew = ref(false);
const d = computed(() => advancesData.data);

const tiles = computed(() => {
	const s = d.value?.stats || {};
	return [
		{
			label: "Outstanding",
			value: money(s.outstanding, { compact: true }),
			hint: "still to repay",
		},
		{
			label: "Repaid",
			value: money(s.repaid, { compact: true }),
			pct: s.pct_repaid,
			hint: `${s.pct_repaid || 0} percent of ${money(s.total, { compact: true })}`,
		},
		{ label: "Taken", value: money(s.total, { compact: true }), hint: "lifetime" },
	];
});

function outstanding(row) {
	if (row.docstatus !== 1) return 0;
	return (row.paid_amount || 0) - (row.claimed_amount || 0) - (row.return_amount || 0);
}

function open(row) {
	router.push(requestPath("advance", row.name));
}

onMounted(() => advancesData.fetch());
</script>
