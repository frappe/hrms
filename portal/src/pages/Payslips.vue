<template>
	<PageBody :loading="payslipsData.loading && !payslipsData.data">
		<PageHead title="Payslips" subtitle="Your salary history" />

		<template v-if="d">
			<StatTiles :tiles="tiles" />

			<DashGrid>
				<template #main>
					<SectionCard title="Monthly Payslips" :padded="false">
						<DataTable
							:columns="cols"
							:rows="d.slips"
							clickable
							empty-message="No payslips have been issued to you yet."
							@row-click="open"
						>
							<template #cell-gross_pay="{ row }">{{
								money(row.gross_pay)
							}}</template>
							<template #cell-total_deduction="{ row }">
								{{ money(row.total_deduction) }}
							</template>
							<template #cell-net_pay="{ row }">
								<span class="font-semibold text-ink-gray-9">{{
									money(row.net_pay)
								}}</span>
							</template>
							<template #cell-status="{ row }">
								<StatusBadge
									:status="row.docstatus === 1 ? row.status : 'Draft'"
								/>
							</template>
						</DataTable>
					</SectionCard>
				</template>

				<template #side>
					<SectionCard title="Tax Declaration">
						<template #action>
							<StatusBadge
								:status="d.tax.has_declaration ? 'submitted' : 'due'"
								:label="d.tax.has_declaration ? 'Submitted' : 'Not declared'"
							/>
						</template>
						<dl class="flex flex-col">
							<FieldRow label="Declared" :value="money(d.tax.declared)" nums />
							<FieldRow
								label="Period ends"
								:value="d.tax.period_end ? date(d.tax.period_end) : ''"
								nums
							/>
						</dl>
						<Button
							variant="subtle"
							class="mt-1 w-full"
							@click="desk('employee-tax-exemption-declaration')"
						>
							Declare Investments
						</Button>
					</SectionCard>

					<SectionCard title="Salary Structure" readonly-label="HR-owned">
						<dl class="flex flex-col">
							<FieldRow
								label="Structure"
								:value="d.structure?.salary_structure"
								locked
							/>
							<FieldRow
								label="Effective"
								:value="d.structure?.from_date ? date(d.structure.from_date) : ''"
								locked
								nums
							/>
						</dl>
					</SectionCard>

					<SectionCard title="Bank Account" action="Edit" @action="$router.push('/me')">
						<dl class="flex flex-col">
							<FieldRow label="Bank" :value="d.bank.bank_name" />
							<FieldRow label="Account" :value="d.bank.account" nums />
							<FieldRow label="IFSC" :value="d.bank.ifsc" />
						</dl>
					</SectionCard>
				</template>
			</DashGrid>
		</template>
	</PageBody>
</template>

<script setup>
import { computed, onMounted } from "vue";
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

import { payslipsData } from "@/data/portal";
import { date, money } from "@/utils/format";

const cols = [
	{ key: "period", label: "Period", primary: true },
	{
		key: "gross_pay",
		label: "Gross",
		align: "right",
		nums: true,
		muted: true,
		hideOnMobile: true,
	},
	{
		key: "total_deduction",
		label: "Deductions",
		align: "right",
		nums: true,
		muted: true,
		hideOnMobile: true,
	},
	{ key: "net_pay", label: "Net Pay", align: "right", nums: true },
	{ key: "status", label: "Status", align: "right", badge: true },
];

const router = useRouter();
const d = computed(() => payslipsData.data);

const tiles = computed(() => {
	const y = d.value?.ytd || {};
	return [
		{
			label: "Gross, Year to Date",
			value: money(y.gross, { compact: true }),
			hint: `${y.months || 0} months paid`,
		},
		{
			label: "Deductions",
			value: money(y.deductions, { compact: true }),
			hint: "tax, PF and other",
		},
		{
			label: "Net Paid",
			value: money(y.net, { compact: true }),
			hint: y.last_paid ? `last ${date(y.last_paid)}` : "",
		},
	];
});

function open(row) {
	router.push(`/payslips/${encodeURIComponent(row.name)}`);
}
function desk(doctype) {
	window.location.href = `/app/${doctype}/new`;
}

onMounted(() => payslipsData.fetch());
</script>
