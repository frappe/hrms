<template>
	<PageBody :loading="payslipsData.loading && !payslipsData.data">
		<PageHead title="Payslips" subtitle="Your salary history">
			<template #actions>
				<!--
					The filter is the selection: whatever the list shows is what
					downloads, so there is no mode to enter and no hidden state.
				-->
				<Button
					variant="subtle"
					icon-left="lucide-download"
					:disabled="!d?.slips?.length"
					:loading="zipping"
					:label="d?.slips?.length ? `Download ${d.slips.length}` : 'Download'"
					@click="downloadAll"
				/>
			</template>
		</PageHead>

		<!-- Custom reveals the two date fields beside the dropdown -->
		<div class="flex flex-wrap items-center gap-2">
			<Select v-model="period" :options="PERIODS" class="w-44" />
			<template v-if="period === 'custom'">
				<DateField v-model="fromDate" placeholder="From" class="w-44" />
				<DateField v-model="toDate" placeholder="To" class="w-44" />
			</template>
			<span v-else-if="d?.range?.from_date" class="text-base text-ink-gray-5">
				{{ date(d.range.from_date) }} to {{ date(d.range.to_date) }}
			</span>
		</div>

		<template v-if="d">
			<StatTiles :tiles="tiles" />

			<DashGrid>
				<template #main>
					<SectionCard title="Monthly Payslips" :padded="false">
						<DataTable
							:columns="cols"
							:rows="d.slips"
							clickable
							empty-message="No payslips in this period."
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
							<template #cell-download="{ row }">
								<!-- stop, or the row's own click would open the payslip too -->
								<Button
									variant="ghost"
									icon="lucide-download"
									:label="`Download ${row.period}`"
									@click.stop="downloadOne(row)"
								/>
							</template>
						</DataTable>
					</SectionCard>
				</template>

				<template #side>
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
				</template>
			</DashGrid>
		</template>
	</PageBody>
</template>

<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { Button, Select } from "frappe-ui";

import PageBody from "@/components/PageBody.vue";
import PageHead from "@/components/PageHead.vue";
import DashGrid from "@/components/DashGrid.vue";
import SectionCard from "@/components/SectionCard.vue";
import DataTable from "@/components/DataTable.vue";
import StatTiles from "@/components/StatTiles.vue";
import StatusBadge from "@/components/StatusBadge.vue";
import FieldRow from "@/components/FieldRow.vue";
import DateField from "@/components/DateField.vue";

import { payslipsData } from "@/data/portal";
import { date, money } from "@/utils/format";
import { errorMessage, notifyError, notifySuccess } from "@/utils/toast";

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
	{ key: "download", label: "", align: "right", track: "2.25rem" },
];

const PERIODS = [
	{ label: "Past 3 months", value: "3m" },
	{ label: "Past 6 months", value: "6m" },
	{ label: "Past year", value: "12m" },
	{ label: "All", value: "all" },
	{ label: "Custom", value: "custom" },
];

const router = useRouter();
const d = computed(() => payslipsData.data);

const period = ref("12m");
const fromDate = ref("");
const toDate = ref("");
const zipping = ref(false);

function load() {
	// a custom range only makes sense once both ends are set
	if (period.value === "custom" && !(fromDate.value && toDate.value)) return;
	payslipsData.fetch({
		period: period.value,
		from_date: fromDate.value || undefined,
		to_date: toDate.value || undefined,
	});
}

watch([period, fromDate, toDate], load);

/**
 * Both paths fetch and save a blob rather than pointing an anchor at the
 * endpoint: a navigation-style download is a second request the dev server
 * can refuse, and the zip is a POST which cannot be navigated to at all.
 */
function saveBlob(blob, filename) {
	const url = URL.createObjectURL(blob);
	const a = document.createElement("a");
	a.href = url;
	a.download = filename;
	a.click();
	URL.revokeObjectURL(url);
}

/** A single slip goes straight to the PDF endpoint; no zip for one file. */
async function downloadOne(row) {
	try {
		const res = await fetch(
			`/api/method/hrms.api.portal.payslip_pdf?name=${encodeURIComponent(row.name)}`,
		);
		if (!res.ok) throw new Error(await res.text());
		saveBlob(await res.blob(), `${row.period.replace(" ", "-")}-payslip.pdf`);
	} catch (e) {
		notifyError("Could not download", errorMessage(e, "Try again in a moment."));
	}
}

function open(row) {
	router.push(`/payslips/${encodeURIComponent(row.name)}`);
}

async function downloadAll() {
	const names = (d.value?.slips || []).map((s) => s.name);
	if (!names.length) return;

	zipping.value = true;
	try {
		const res = await fetch("/api/method/hrms.api.portal.payslips_zip", {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
				Accept: "application/json",
				"X-Frappe-CSRF-Token": window.csrf_token,
			},
			body: JSON.stringify({ names }),
		});
		if (!res.ok) throw new Error(await res.text());

		saveBlob(await res.blob(), "payslips.zip");
		notifySuccess(`${names.length} payslips downloaded`);
	} catch (e) {
		notifyError("Could not download", errorMessage(e, "Try again in a moment."));
	} finally {
		zipping.value = false;
	}
}

onMounted(() => payslipsData.fetch());
</script>
