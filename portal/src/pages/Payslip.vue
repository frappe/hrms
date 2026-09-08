<template>
	<PageBody :loading="payslipData.loading && !payslipData.data">
		<template v-if="d">
			<PageHead
				:subtitle="`${dateRange(d.start_date, d.end_date)} · paid ${date(d.posting_date)}`"
				:crumbs="[{ label: 'Payslips', to: '/payslips' }, { label: d.period }]"
			>
				<template #actions>
					<Button
						variant="subtle"
						icon="download"
						label="Download PDF"
						@click="download"
					/>
					<Button variant="subtle" icon="printer" label="Print" @click="print" />
				</template>
			</PageHead>

			<StatTiles :tiles="tiles" />

			<DashGrid>
				<template #main>
					<SectionCard title="Earnings" :padded="false">
						<DataTable
							:columns="cols"
							:rows="d.earnings"
							id-key="salary_component"
							empty-message="No earnings on this payslip."
						>
							<template #cell-amount="{ row }">{{ amount(row.amount) }}</template>
							<template #cell-year_to_date="{ row }">{{
								amount(row.year_to_date)
							}}</template>
						</DataTable>
						<TotalRow label="Gross Pay" :value="amount(d.gross_pay)" />
					</SectionCard>

					<SectionCard title="Deductions" :padded="false">
						<DataTable
							:columns="cols"
							:rows="d.deductions"
							id-key="salary_component"
							empty-message="Nothing was deducted."
						>
							<template #cell-amount="{ row }">{{ amount(row.amount) }}</template>
							<template #cell-year_to_date="{ row }">{{
								amount(row.year_to_date)
							}}</template>
						</DataTable>
						<TotalRow label="Total Deductions" :value="amount(d.total_deduction)" />
					</SectionCard>

					<SectionCard title="Net Pay" :padded="false">
						<TotalRow
							label="Take home"
							:value="amount(d.rounded_total || d.net_pay)"
							strong
						/>
						<p v-if="d.total_in_words" class="px-3.5 pb-3.5 text-sm text-ink-gray-5">
							{{ d.total_in_words }}
						</p>
					</SectionCard>
				</template>

				<template #side>
					<SectionCard title="Status">
						<template #action>
							<StatusBadge :status="d.status" />
						</template>
						<dl class="flex flex-col">
							<FieldRow label="Period" :value="d.period" />
							<FieldRow label="Paid on" :value="date(d.posting_date)" nums />
							<FieldRow label="Mode" :value="d.mode_of_payment" />
							<FieldRow label="Account" :value="d.bank_account" nums />
						</dl>
					</SectionCard>

					<SectionCard title="Days" readonly-label="HR-owned">
						<dl class="flex flex-col">
							<FieldRow
								label="Working days"
								:value="days(a.total_working_days)"
								locked
								nums
							/>
							<FieldRow
								label="Payable days"
								:value="days(a.payment_days)"
								locked
								nums
							/>
							<FieldRow
								label="Unpaid leave"
								:value="days(a.leave_without_pay)"
								locked
								nums
							/>
							<FieldRow label="Absent" :value="days(a.absent_days)" locked nums />
						</dl>
					</SectionCard>

					<SectionCard title="Year to Date">
						<dl class="flex flex-col">
							<FieldRow label="Gross" :value="amount(d.gross_year_to_date)" nums />
							<FieldRow label="Net" :value="amount(d.year_to_date)" nums />
						</dl>
					</SectionCard>

					<SectionCard title="Salary Structure" readonly-label="HR-owned">
						<dl class="flex flex-col">
							<FieldRow label="Structure" :value="d.salary_structure" locked />
						</dl>
					</SectionCard>
				</template>
			</DashGrid>
		</template>
	</PageBody>
</template>

<script setup>
import { computed, onMounted, watch } from "vue";
import { useRoute } from "vue-router";
import { Button } from "frappe-ui";

import PageBody from "@/components/PageBody.vue";
import PageHead from "@/components/PageHead.vue";
import DashGrid from "@/components/DashGrid.vue";
import SectionCard from "@/components/SectionCard.vue";
import DataTable from "@/components/DataTable.vue";
import StatTiles from "@/components/StatTiles.vue";
import StatusBadge from "@/components/StatusBadge.vue";
import FieldRow from "@/components/FieldRow.vue";
import TotalRow from "@/components/TotalRow.vue";

import { payslipData } from "@/data/portal";
import { date, dateRange, money } from "@/utils/format";

const route = useRoute();

const d = computed(() => payslipData.data);
const a = computed(() => d.value?.attendance || {});

const cols = [
	{ key: "salary_component", label: "Component", primary: true },
	{ key: "amount", label: "Amount", align: "right", nums: true },
	{
		key: "year_to_date",
		label: "Year to Date",
		align: "right",
		nums: true,
		muted: true,
		hideOnMobile: true,
	},
];

const tiles = computed(() => [
	{ label: "Gross Pay", value: amount(d.value?.gross_pay) },
	{ label: "Deductions", value: amount(d.value?.total_deduction) },
	{
		label: "Net Pay",
		value: amount(d.value?.rounded_total || d.value?.net_pay),
		hint: d.value?.period,
	},
]);

/** every figure on a payslip is in the slip's own currency, not the company's */
function amount(value) {
	return money(value, { currency: d.value?.currency });
}

function days(value) {
	if (value === null || value === undefined) return "—";
	return Number(value) === 1 ? "1 day" : `${Number(value)} days`;
}

/**
 * Both actions render server-side through the print format desk is set to use.
 * They go through the portal's own endpoint rather than frappe's download_pdf
 * so that the "your documents only" rule holds here too.
 */
function pdfUrl(inline) {
	const params = new URLSearchParams({ name: d.value.name });
	if (inline) params.set("inline", "1");
	return `/api/method/hrms.api.portal.payslip_pdf?${params}`;
}

function print() {
	window.open(pdfUrl(true), "_blank", "noopener");
}

function download() {
	const a = document.createElement("a");
	a.href = pdfUrl(false);
	a.rel = "noopener";
	a.click();
}

function load() {
	payslipData.fetch({ name: route.params.name });
}

onMounted(load);
watch(() => route.params.name, load);
</script>
