<template>
	<PageBody :loading="homeData.loading && !homeData.data">
		<!-- no header actions: check-in is the hero, and the quick action grid covers the rest -->
		<PageHead :title="greeting" :subtitle="today" />

		<!--
			One column at the desk page width: a side rail would leave the requests
			table about 520px wide, too narrow for five columns.
		-->
		<template v-if="d">
			<CheckInCard :checkin="d.checkin" :week="d.week" @changed="homeData.reload()" />

			<!--
				Only for someone who was actually onboarded, and only while
				something is still outstanding. Most of these tasks belong to HR or
				IT, so this is where a new joiner sees what is still being done for
				them rather than having to ask.
			-->
			<SectionCard v-if="d.onboarding" title="Onboarding" :padded="false">
				<template #action>
					<div class="flex items-center gap-2.5">
						<span class="nums text-base text-ink-gray-5">
							{{ d.onboarding.done }} of {{ d.onboarding.total }} done
						</span>
						<StatusBadge :status="d.onboarding.status" />
					</div>
				</template>
				<Progress class="px-3.5 pb-2.5" :value="d.onboarding.pct" size="md" />
				<DataTable :columns="onboardingCols" :rows="d.onboarding.tasks" id-key="activity">
					<template #cell-activity="{ row }">
						<span class="text-ink-gray-8">{{ row.activity }}</span>
					</template>
					<template #cell-owner="{ row }">
						<span :class="row.mine ? 'text-ink-gray-8' : 'text-ink-gray-6'">
							{{ row.owner }}
						</span>
					</template>
					<template #cell-due="{ row }">
						<span class="nums text-ink-gray-5">{{
							row.due ? date(row.due) : "—"
						}}</span>
					</template>
					<template #cell-status="{ row }">
						<StatusBadge :status="row.status" />
					</template>
				</DataTable>
			</SectionCard>

			<div class="grid grid-cols-2 gap-3 sm:grid-cols-3">
				<RouterLink
					v-for="a in ACTIONS"
					:key="a.label"
					:to="a.to"
					class="flex items-center gap-2.5 rounded-6 border border-outline-gray-1 bg-surface-base p-3 transition-colors hover:bg-surface-gray-1"
				>
					<span
						class="flex h-7 w-7 shrink-0 items-center justify-center rounded-4 bg-surface-gray-3 text-ink-gray-7"
					>
						<span :class="[a.icon, 'h-3.5 w-3.5']" aria-hidden="true" />
					</span>
					<span class="text-base leading-tight text-ink-gray-8">{{ a.label }}</span>
				</RouterLink>
			</div>

			<!-- approvers only, and absent at zero rather than showing an empty state -->
			<SectionCard v-if="d.pending_approvals?.length" title="Waiting on You">
				<template #action>
					<StatusBadge status="pending" :label="String(d.pending_approvals.length)" />
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
						<span
							class="h-3.5 w-3.5 shrink-0 text-ink-gray-4 lucide-chevron-right"
							aria-hidden="true"
						/>
					</li>
				</ul>
			</SectionCard>

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
	</PageBody>
</template>

<script setup>
import { computed, onMounted } from "vue";
import { Button, Progress } from "frappe-ui";

import PageBody from "@/components/PageBody.vue";
import PageHead from "@/components/PageHead.vue";
import SectionCard from "@/components/SectionCard.vue";
import DataTable from "@/components/DataTable.vue";
import StatusBadge from "@/components/StatusBadge.vue";
import PersonRow from "@/components/PersonRow.vue";
import FieldRow from "@/components/FieldRow.vue";
import EmptyState from "@/components/EmptyState.vue";
import CheckInCard from "@/components/CheckInCard.vue";

import { homeData } from "@/data/portal";
import { date, dateRange, dayjs, money } from "@/utils/format";

const onboardingCols = [
	{ key: "activity", label: "Task", primary: true },
	{ key: "owner", label: "With", muted: true, hideOnMobile: true },
	{ key: "due", label: "Due", align: "right", nums: true, hideOnMobile: true },
	{ key: "status", label: "Status", align: "right", badge: true },
];

const ACTIONS = [
	{ label: "Apply Leave", to: "/leave", icon: "lucide-sunrise" },
	{ label: "Claim Expense", to: "/expenses", icon: "lucide-credit-card" },
	{ label: "Latest Payslips", to: "/payslips", icon: "lucide-file-text" },
	{ label: "Request Advance", to: "/advances", icon: "lucide-trending-up" },
	{ label: "Regularise", to: "/attendance", icon: "lucide-clock" },
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
