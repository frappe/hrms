<template>
	<!--
		frappe-ui/list in column mode. Header and rows share one --list-columns
		template so they cannot drift. Below sm the template is overridden to two
		tracks and every column but the primary and the badge drops out, which is
		the documented way to collapse a table list rather than keep a second
		markup tree for mobile.
	-->
	<List
		v-if="rows.length"
		v-model:selection="selection"
		:columns="tracks"
		:row-height="40"
		:selectable="selectable"
		class="list-row-px-3.5 max-sm:[--list-columns:minmax(0,1fr)_auto]"
	>
		<!--
			`!` is load-bearing: the package sets display:grid on
			[data-slot='list-header'] with a bare attribute selector, which ties with
			a utility class on specificity and wins on order.
		-->
		<ListHeader class="max-sm:!hidden">
			<!-- the label is the default slot, not a prop -->
			<ListHeaderCell
				v-for="col in columns"
				:key="col.key"
				:class="[layoutClass(col), 'text-base']"
			>
				{{ col.label }}
			</ListHeaderCell>
		</ListHeader>

		<ListRows :items="rows" :row-key="idKey" v-slot="{ item, value }">
			<ListRow :value="value" @click="clickable && $emit('row-click', item)">
				<ListCell v-for="col in columns" :key="col.key" :class="cellClass(col)">
					<!--
						The truncate wraps the slot, not just the fallback: rows are a
						fixed height, so cell content that wrapped to a second line would
						be clipped mid-glyph instead of ending in an ellipsis.
					-->
					<span class="truncate">
						<slot :name="`cell-${col.key}`" :row="item">{{ display(item, col) }}</slot>
					</span>
				</ListCell>
			</ListRow>
		</ListRows>
	</List>

	<div v-else class="px-3.5 pb-3.5">
		<EmptyState :message="emptyMessage" />
	</div>
</template>

<script setup>
import { computed } from "vue";
import { List, ListCell, ListHeader, ListHeaderCell, ListRow, ListRows } from "frappe-ui/list";
import EmptyState from "@/components/EmptyState.vue";

const props = defineProps({
	columns: { type: Array, default: () => [] },
	rows: { type: Array, default: () => [] },
	emptyMessage: { type: String, default: "Nothing here yet." },
	clickable: Boolean,
	selectable: Boolean,
	idKey: { type: String, default: "name" },
});
defineEmits(["row-click"]);

// `selectable` reveals the checkbox column and switches row click from
// navigate to toggle, so the two are mutually exclusive by construction.
const selection = defineModel("selection", { type: Array, default: () => [] });

/**
 * Every track has to be deterministic: each row is its own grid, so an `auto`
 * track would size independently per row and the columns would not line up.
 */
const tracks = computed(() =>
	props.columns.map((col) => {
		if (col.track) return col.track;
		// fr, not fixed rem: a five-column list inside a ~500px card would
		// otherwise total more than the container and spill over the next one
		if (col.primary) return "minmax(6rem,2fr)";
		if (col.align === "right" || col.badge) return "minmax(4rem,1fr)";
		return "minmax(5rem,1fr)";
	}),
);

/**
 * Geometry only, shared by the header and the rows. Cells are flex with
 * items-center, so alignment is a justify utility.
 */
function layoutClass(col) {
	return [
		col.align === "right" ? "justify-end" : "justify-start",
		// the mobile template has room for the primary column and the badge only
		!col.primary && !col.badge && "max-sm:hidden",
	];
}

/**
 * The list family owns geometry and nothing readable, so cell typography is
 * ours to set: without text-base these inherit the browser's 16px while the
 * rest of the app runs at 14px.
 */
function cellClass(col) {
	return [
		...layoutClass(col),
		"text-base",
		col.nums && "nums",
		col.muted ? "text-ink-gray-5" : "text-ink-gray-8",
		col.strong && "font-semibold text-ink-gray-9",
	];
}

function display(row, col) {
	const value = row?.[col.key];
	return value === null || value === undefined || value === "" ? "—" : value;
}
</script>
