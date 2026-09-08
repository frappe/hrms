<template>
	<PageBody :loading="requestData.loading && !requestData.data">
		<template v-if="d">
			<PageHead
				:subtitle="`${d.editable ? 'Raised' : 'Submitted'} ${date(d.posting_date)}`"
				:crumbs="[{ label: d.label, to: d.list_route }, { label: d.name }]"
			>
				<template #actions>
					<Button v-if="d.editable" variant="ghost" theme="red" @click="confirmDelete"
						>Delete</Button
					>
					<Button v-if="d.editable" variant="solid" @click="showEdit = true"
						>Edit</Button
					>
				</template>
			</PageHead>

			<StatTiles :tiles="tiles" />

			<DashGrid>
				<template #main>
					<!-- child rows get a table; a flat document gets a field list -->
					<SectionCard v-if="rows" :title="rowsLabel" :padded="false">
						<DataTable :columns="rowCols" :rows="rows" id-key="idx">
							<template
								v-for="col in rowCols"
								:key="col.key"
								#[`cell-${col.key}`]="{ row }"
							>
								{{ cellText(col, row) }}
							</template>
						</DataTable>
					</SectionCard>

					<SectionCard v-else title="Details">
						<dl class="flex flex-col">
							<FieldRow
								v-for="f in detailFields"
								:key="f.fieldname"
								:label="f.label"
								:value="fieldText(f)"
							/>
						</dl>
					</SectionCard>

					<SectionCard v-if="d.supports_attachments" title="Attachments" :padded="false">
						<ul v-if="d.attachments.length">
							<li
								v-for="a in d.attachments"
								:key="a.name"
								class="flex items-center justify-between gap-3 border-b border-outline-gray-1 px-3.5 py-2.5 last:border-0"
							>
								<a
									:href="a.file_url"
									target="_blank"
									rel="noopener"
									class="flex min-w-0 items-center gap-2 text-p-base text-ink-gray-8 hover:underline"
								>
									<FeatherIcon
										name="paperclip"
										class="h-3.5 w-3.5 shrink-0 text-ink-gray-4"
									/>
									<span class="truncate">{{ a.file_name }}</span>
								</a>
								<span class="nums shrink-0 text-base text-ink-gray-5">
									{{ fileSize(a.file_size) }}
								</span>
							</li>
						</ul>
						<div v-else class="px-3.5 pb-3.5">
							<EmptyState message="Nothing attached." />
						</div>
					</SectionCard>
				</template>

				<template #side>
					<SectionCard title="Status">
						<template #action>
							<StatusBadge :status="d.display_status" />
						</template>
						<dl class="flex flex-col">
							<FieldRow
								v-if="d.approver_name"
								label="Approver"
								:value="d.approver_name"
							/>
							<FieldRow label="Raised on" :value="date(d.posting_date)" nums />
						</dl>
						<p v-if="d.editable" class="text-base text-ink-gray-5">
							This is still a draft. Your approver reviews and submits it.
						</p>
					</SectionCard>

					<SectionCard v-if="rows" title="Summary">
						<dl class="flex flex-col">
							<FieldRow
								v-for="s in d.summary"
								:key="s.label"
								:label="s.label"
								:value="summaryText(s)"
								nums
							/>
						</dl>
					</SectionCard>
				</template>
			</DashGrid>

			<RequestDialog
				v-model:open="showEdit"
				:type="d.type"
				:request="d"
				:currency="d.currency"
				@saved="reload"
			/>
		</template>
	</PageBody>
</template>

<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { Button, FeatherIcon, confirmDialog } from "frappe-ui";

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

import { deleteRequest, requestData, requestForm } from "@/data/requests";
import { date, money } from "@/utils/format";
import { errorMessage, notifyError, notifySuccess } from "@/utils/toast";

const route = useRoute();
const router = useRouter();
const showEdit = ref(false);
const schema = ref(null);

const d = computed(() => requestData.data);

const tableField = computed(() => (schema.value?.fields || []).find((f) => f.type === "table"));
const detailFields = computed(() =>
	(schema.value?.fields || []).filter((f) => f.type !== "table"),
);

const rows = computed(() =>
	tableField.value ? d.value?.values?.[tableField.value.fieldname] : null,
);
const rowsLabel = computed(() => tableField.value?.label || "Items");

const rowCols = computed(() =>
	(tableField.value?.fields || []).map((f, i) => ({
		key: f.fieldname,
		label: f.label,
		primary: i === 0,
		nums: f.type === "number" || f.type === "date",
		align: f.type === "number" ? "right" : "left",
		fieldType: f.type,
	})),
);

const tiles = computed(() => {
	if (!d.value) return [];
	const out = d.value.summary.slice(0, 3).map((s) => ({
		label: s.label,
		value: summaryText(s),
	}));
	out.push({
		label: "Status",
		value: d.value.display_status,
		hint: d.value.editable ? "with your approver" : "",
	});
	return out.slice(0, 4);
});

function summaryText(s) {
	if (s.kind === "money") return money(s.value, { currency: s.currency || d.value?.currency });
	if (s.kind === "date") return date(s.value);
	return s.value ?? "—";
}

function cellText(col, row) {
	const v = row[col.key];
	if (v === null || v === undefined || v === "") return "—";
	if (col.fieldType === "date") return date(v);
	if (col.fieldType === "number") return money(v, { currency: d.value?.currency });
	return v;
}

function fieldText(f) {
	const v = d.value?.values?.[f.fieldname];
	if (f.type === "checkbox") return v ? "Yes" : "No";
	if (f.type === "date") return v ? date(v) : "";
	if (f.type === "number") return money(v, { currency: d.value?.currency });
	return v;
}

function fileSize(bytes) {
	if (!bytes) return "—";
	if (bytes >= 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
	return `${Math.max(1, Math.round(bytes / 1024))} KB`;
}

async function reload() {
	const { type, name } = route.params;
	requestData.fetch({ request_type: type, name });
	schema.value = await requestForm.fetch({ request_type: type });
}

function confirmDelete() {
	const { label, name, type, list_route } = d.value;
	confirmDialog({
		title: `Delete this ${label.toLowerCase()}?`,
		message: `${name} will be removed. This cannot be undone.`,
		async onConfirm({ hideDialog }) {
			try {
				await deleteRequest.submit({ request_type: type, name });
				notifySuccess(`${label} deleted`);
				hideDialog();
				router.push(list_route);
			} catch (e) {
				notifyError("Could not delete", errorMessage(e, "Try again in a moment."));
			}
		},
	});
}

onMounted(reload);
watch(() => [route.params.type, route.params.name], reload);
</script>
