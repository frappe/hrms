<template>
	<PageBody :loading="documentsData.loading && !documentsData.data">
		<PageHead title="Documents" subtitle="Company files and your own records" />

		<template v-if="d">
			<DashGrid ratio="even">
				<template #main>
					<SectionCard title="Company Documents" :padded="false">
						<DataTable
							:columns="companyCols"
							:rows="d.company"
							clickable
							empty-message="No company-wide documents have been shared yet."
							@row-click="open"
						>
							<template #cell-modified="{ row }">{{ date(row.modified) }}</template>
							<template #cell-file_size="{ row }">{{
								size(row.file_size)
							}}</template>
						</DataTable>
					</SectionCard>
				</template>

				<template #side>
					<!-- personal files live on the profile; this is a pointer, not a duplicate -->
					<SectionCard title="Issued to You" :padded="false">
						<template #action>
							<Button variant="ghost" route="/me" label="Open Profile" />
						</template>
						<DataTable
							:columns="mineCols"
							:rows="d.mine"
							clickable
							empty-message="No documents are attached to your employee record."
							@row-click="open"
						>
							<template #cell-modified="{ row }">{{ date(row.modified) }}</template>
							<template #cell-is_private="{ row }">
								<StatusBadge
									:status="row.is_private ? 'gray' : 'available'"
									:label="row.is_private ? 'Private' : 'Shared'"
								/>
							</template>
						</DataTable>
					</SectionCard>
				</template>
			</DashGrid>
		</template>
	</PageBody>
</template>

<script setup>
import { Button } from "frappe-ui";
import { computed, onMounted } from "vue";

import PageBody from "@/components/PageBody.vue";
import PageHead from "@/components/PageHead.vue";
import DashGrid from "@/components/DashGrid.vue";
import SectionCard from "@/components/SectionCard.vue";
import DataTable from "@/components/DataTable.vue";
import StatusBadge from "@/components/StatusBadge.vue";

import { documentsData } from "@/data/portal";
import { date } from "@/utils/format";

const companyCols = [
	{ key: "file_name", label: "Document", primary: true },
	{ key: "file_size", label: "Size", nums: true, muted: true, hideOnMobile: true },
	{ key: "modified", label: "Updated", nums: true, muted: true, align: "right" },
];

const mineCols = [
	{ key: "file_name", label: "File", primary: true },
	{ key: "modified", label: "Added", nums: true, muted: true },
	{ key: "is_private", label: "", align: "right", badge: true },
];

const d = computed(() => documentsData.data);

function size(bytes) {
	if (!bytes) return "—";
	if (bytes < 1024) return `${bytes} B`;
	if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
	return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function open(row) {
	if (row.file_url) window.open(row.file_url, "_blank", "noopener");
}

onMounted(() => documentsData.fetch());
</script>
