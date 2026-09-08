<template>
	<div>
		<!-- a real table from md up -->
		<div class="scroll-x hidden md:block">
			<table class="w-full border-collapse">
				<thead>
					<tr>
						<th
							v-for="col in columns"
							:key="col.key"
							class="whitespace-nowrap border-b border-outline-gray-1 px-3.5 py-2 text-base font-medium text-ink-gray-5"
							:class="col.align === 'right' ? 'text-right' : 'text-left'"
						>
							{{ col.label }}
						</th>
					</tr>
				</thead>
				<tbody>
					<tr
						v-for="(row, i) in rows"
						:key="rowKey(row, i)"
						class="border-b border-outline-gray-1 last:border-0"
						:class="clickable && 'cursor-pointer hover:bg-surface-gray-1'"
						@click="clickable && $emit('row-click', row)"
					>
						<td
							v-for="col in columns"
							:key="col.key"
							class="px-3.5 py-2.5 text-p-base text-ink-gray-8"
							:class="[
								col.align === 'right' ? 'text-right' : 'text-left',
								col.nums && 'nums',
								col.muted && 'text-ink-gray-5',
								col.strong && 'font-semibold text-ink-gray-9',
							]"
						>
							<slot :name="`cell-${col.key}`" :row="row">
								{{ display(row, col) }}
							</slot>
						</td>
					</tr>
				</tbody>
			</table>
		</div>

		<!-- stacked rows below md: same slots, different shape -->
		<ul class="md:hidden">
			<li
				v-for="(row, i) in rows"
				:key="rowKey(row, i)"
				class="flex items-start justify-between gap-3 border-b border-outline-gray-1 px-3.5 py-2.5 last:border-0"
				:class="clickable && 'cursor-pointer'"
				@click="clickable && $emit('row-click', row)"
			>
				<div class="min-w-0">
					<div class="text-p-base text-ink-gray-8">
						<slot :name="`cell-${primaryCol.key}`" :row="row">
							{{ display(row, primaryCol) }}
						</slot>
					</div>
					<div
						class="mt-0.5 flex flex-wrap items-center gap-x-2 text-base text-ink-gray-5"
					>
						<!-- a stacked row has no column headers, so a bare dash reads as noise -->
						<span
							v-for="col in secondaryCols"
							:key="col.key"
							v-show="hasValue(row, col)"
							:class="col.nums && 'nums'"
						>
							<slot :name="`cell-${col.key}`" :row="row">
								{{ display(row, col) }}
							</slot>
						</span>
					</div>
				</div>
				<div v-if="badgeCol" class="shrink-0">
					<slot :name="`cell-${badgeCol.key}`" :row="row">
						{{ display(row, badgeCol) }}
					</slot>
				</div>
			</li>
		</ul>

		<div v-if="!rows.length" class="px-3.5 pb-3.5">
			<EmptyState :message="emptyMessage" />
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue";
import EmptyState from "@/components/EmptyState.vue";

const props = defineProps({
	columns: { type: Array, default: () => [] },
	rows: { type: Array, default: () => [] },
	emptyMessage: { type: String, default: "Nothing here yet." },
	clickable: Boolean,
	idKey: { type: String, default: "name" },
});
defineEmits(["row-click"]);

const primaryCol = computed(
	() => props.columns.find((c) => c.primary) || props.columns[0] || { key: "" },
);
const badgeCol = computed(() => props.columns.find((c) => c.badge));
const secondaryCols = computed(() =>
	props.columns.filter((c) => c !== primaryCol.value && c !== badgeCol.value && !c.hideOnMobile),
);

function rowKey(row, i) {
	return row?.[props.idKey] ?? i;
}

function display(row, col) {
	const value = row?.[col.key];
	return value === null || value === undefined || value === "" ? "—" : value;
}

function hasValue(row, col) {
	const value = row?.[col.key];
	return value !== null && value !== undefined && value !== "";
}
</script>
