<template>
	<PageBody :loading="homeData.loading && !homeData.data">
		<!-- no header actions: check-in is the hero, and the quick action grid covers the rest -->
		<PageHead :title="greeting" :subtitle="today" />

		<DashGrid v-if="d">
			<template #main>
				<CheckInCard :checkin="d.checkin" :week="d.week" @changed="homeData.reload()" />

				<div class="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
					<RouterLink
						v-for="a in ACTIONS"
						:key="a.label"
						:to="a.to"
						class="flex items-center gap-2.5 rounded-lg border border-outline-gray-1 bg-surface-white p-3 transition-colors hover:bg-surface-gray-1"
					>
						<span
							class="flex h-7 w-7 shrink-0 items-center justify-center rounded bg-surface-gray-3 text-ink-gray-7"
						>
							<FeatherIcon :name="a.icon" class="h-3.5 w-3.5" />
						</span>
						<span class="text-base leading-tight text-ink-gray-8">{{ a.label }}</span>
					</RouterLink>
				</div>

				<SectionCard title="My Requests" :padded="false">
					<template #action>
						<Button variant="ghost" route="/leave" label="View All" />
					</template>
					<DataTable
						:columns="requestCols"
						:rows="d.requests"
						empty-message="You have not raised any requests yet."
					>
						<template #cell-detail="{ row }">
							<span class="text-ink-gray-8">{{ detailOf(row) }}</span>
						</template>
						<template #cell-submitted="{ row }">
							<span class="nums text-ink-gray-5">{{ date(row.submitted) }}</span>
						</template>
						<template #cell-approver="{ row }">
							<span class="text-ink-gray-6">{{ row.approver_name || "—" }}</span>
						</template>
						<template #cell-status="{ row }">
							<StatusBadge :status="row.status" />
						</template>
					</DataTable>
				</SectionCard>
			</template>

			<template #side>
				<!-- approvers only, and absent at zero rather than showing an empty state -->
				<SectionCard v-if="d.pending_approvals?.length" title="Waiting on You">
					<template #action>
						<StatusBadge
							status="pending"
							:label="String(d.pending_approvals.length)"
						/>
					</template>
					<ul class="flex flex-col gap-2.5">
						<li
							v-for="p in d.pending_approvals"
							:key="p.name"
							class="flex items-center justify-between gap-2"
						>
							<PersonRow
								:name="p.employee_name"
								:meta="`${p.type}, ${p.detail}`"
								size="md"
							/>
							<FeatherIcon
								name="chevron-right"
								class="h-3.5 w-3.5 shrink-0 text-ink-gray-4"
							/>
						</li>
					</ul>
				</SectionCard>

				<SectionCard title="Leave Balance" action="Apply" @action="$router.push('/leave')">
					<BalanceBars :balances="d.balances" />
				</SectionCard>

				<SectionCard title="Out Today">
					<template #action>
						<span class="text-base text-ink-gray-5">
							{{ d.out_today.count }} of {{ d.out_today.total }}
						</span>
					</template>
					<ul v-if="d.out_today.people.length" class="flex flex-col gap-2">
						<li
							v-for="p in d.out_today.people"
							:key="p.employee"
							class="flex items-center justify-between gap-2"
						>
							<PersonRow
								:name="p.employee_name"
								:to="`/directory/${p.employee}`"
								size="md"
							/>
							<StatusBadge status="on leave" :label="p.reason" />
						</li>
					</ul>
					<EmptyState v-else message="Everybody is in today." />
				</SectionCard>

				<SectionCard title="Coming Up">
					<dl v-if="d.coming_up.length" class="flex flex-col">
						<FieldRow
							v-for="c in d.coming_up"
							:key="c.date + c.label"
							:label="shortDate(c.date)"
							:value="c.label"
						/>
					</dl>
					<EmptyState v-else message="Nothing in the next 60 days." />
				</SectionCard>
			</template>
		</DashGrid>
	</PageBody>
</template>

<script setup>
import { computed, onMounted } from "vue";
import { Button, FeatherIcon } from "frappe-ui";

import PageBody from "@/components/PageBody.vue";
import PageHead from "@/components/PageHead.vue";
import DashGrid from "@/components/DashGrid.vue";
import SectionCard from "@/components/SectionCard.vue";
import DataTable from "@/components/DataTable.vue";
import StatusBadge from "@/components/StatusBadge.vue";
import PersonRow from "@/components/PersonRow.vue";
import BalanceBars from "@/components/BalanceBars.vue";
import FieldRow from "@/components/FieldRow.vue";
import EmptyState from "@/components/EmptyState.vue";
import CheckInCard from "@/components/CheckInCard.vue";

import { homeData } from "@/data/portal";
import { date, dateRange, dayjs, money } from "@/utils/format";

const ACTIONS = [
	{ label: "Apply Leave", to: "/leave", icon: "sunrise" },
	{ label: "Claim Expense", to: "/expenses", icon: "credit-card" },
	{ label: "Latest Payslip", to: "/payslips", icon: "file-text" },
	{ label: "Request Advance", to: "/advances", icon: "trending-up" },
	{ label: "Regularise", to: "/attendance", icon: "clock" },
];

const requestCols = [
	{ key: "type", label: "Type", hideOnMobile: true },
	{ key: "detail", label: "Detail", primary: true },
	{ key: "submitted", label: "Submitted", nums: true, muted: true },
	{ key: "approver", label: "Approver" },
	{ key: "status", label: "Status", align: "right", badge: true },
];

const d = computed(() => homeData.data);

function detailOf(row) {
	if (row.type === "Expense") return money(row.amount);
	const span = dateRange(row.from_date, row.to_date);
	return row.label ? `${row.label}, ${span}` : span;
}

const greeting = computed(() => {
	const h = dayjs().hour();
	const part = h < 12 ? "Good morning" : h < 17 ? "Good afternoon" : "Good evening";
	return `${part}, ${d.value?.greeting_name || ""}`.trim().replace(/,$/, "");
});

const today = computed(() => date(d.value?.today, "dddd, D MMMM YYYY"));

function shortDate(value) {
	return dayjs(value).format("D MMM");
}

onMounted(() => homeData.fetch());
</script>
