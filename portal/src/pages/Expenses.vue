<template>
	<PageBody :loading="expensesData.loading && !expensesData.data">
		<PageHead title="Expenses" subtitle="Your claims and reimbursements">
			<template #actions>
				<Button variant="solid" @click="showNew = true">New Claim</Button>
			</template>
		</PageHead>

		<template v-if="d">
			<StatTiles :tiles="tiles" />

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

			<!-- both absent at zero rather than showing an empty state -->
			<SectionCard
				v-if="d.awaiting_claims?.length"
				title="With Your Approver"
				:padded="false"
			>
				<template #action>
					<StatusBadge status="pending" :label="`${d.awaiting_claims.length}`" />
				</template>
				<ul>
					<li
						v-for="c in d.awaiting_claims"
						:key="c.name"
						class="flex items-center justify-between gap-3 border-b border-outline-gray-1 px-3.5 py-2.5 last:border-0"
					>
						<div class="min-w-0">
							<div class="truncate text-p-base text-ink-gray-8">
								{{ c.purpose || c.name }}
							</div>
							<div class="truncate text-base text-ink-gray-5">
								{{ c.approver_name || "No approver set" }}
							</div>
						</div>
						<div class="shrink-0 text-right">
							<div class="nums text-p-base text-ink-gray-9">
								{{ money(c.amount, { currency: c.currency }) }}
							</div>
							<div class="nums text-base text-ink-gray-5">
								{{ waitingFor(c.days) }}
							</div>
						</div>
					</li>
				</ul>
			</SectionCard>

			<SectionCard v-if="d.advances?.outstanding" title="Advance to Settle" :padded="false">
				<template #action>
					<Button variant="ghost" route="/advances" label="View all" />
				</template>
				<ul>
					<li
						v-for="a in d.advances.rows"
						:key="a.name"
						class="flex items-center justify-between gap-3 border-b border-outline-gray-1 px-3.5 py-2.5 last:border-0"
					>
						<div class="min-w-0">
							<div class="truncate text-p-base text-ink-gray-8">
								{{ a.purpose || a.name }}
							</div>
							<div class="nums truncate text-base text-ink-gray-5">
								{{ money(a.paid_amount) }} advanced on {{ date(a.posting_date) }}
							</div>
						</div>
						<div class="nums shrink-0 text-p-base text-ink-gray-9">
							{{ money(a.outstanding) }}
						</div>
					</li>
				</ul>
				<TotalRow label="Still to settle" :value="money(d.advances.outstanding)" />
				<p class="px-3.5 pb-3.5 text-sm text-ink-gray-5">
					Claim against an advance and this settles automatically.
				</p>
			</SectionCard>
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
import SectionCard from "@/components/SectionCard.vue";
import DataTable from "@/components/DataTable.vue";
import StatTiles from "@/components/StatTiles.vue";
import StatusBadge from "@/components/StatusBadge.vue";
import TotalRow from "@/components/TotalRow.vue";
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

function waitingFor(days) {
	if (days === null || days === undefined) return "";
	if (days === 0) return "today";
	return days === 1 ? "1 day" : `${days} days`;
}

function open(row) {
	router.push(requestPath("expense", row.name));
}

onMounted(() => expensesData.fetch());
</script>
