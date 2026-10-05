<template>
	<div class="flex flex-col gap-0.5 rounded-5 border border-outline-gray-1 p-1">
		<component
			:is="row.route ? RouterLink : 'div'"
			v-for="row in rows"
			:key="row.key"
			:to="row.route"
			:class="row.route ? ROW : ROW_STATIC"
		>
			<Avatar
				v-if="row.lead.kind === 'person'"
				:image="row.lead.image ?? undefined"
				:label="row.lead.name"
				size="md"
				class="shrink-0"
			/>
			<span
				v-else-if="row.lead.kind === 'icon'"
				class="flex size-6 shrink-0 items-center justify-center rounded-full bg-surface-gray-2 text-ink-gray-6"
				aria-hidden="true"
			>
				<span :class="[row.lead.icon, 'size-3.5']" />
			</span>
			<div
				v-else-if="row.lead.kind === 'date'"
				class="flex size-10 shrink-0 flex-col items-center justify-center rounded-4 border"
				:class="
					row.lead.muted
						? 'border-outline-gray-1 bg-surface-gray-1'
						: 'border-outline-gray-2 bg-surface-base'
				"
			>
				<span class="text-2xs font-medium text-ink-red-5" style="line-height: 1">{{
					row.lead.month
				}}</span>
				<span
					class="mt-0.5 text-base-semibold tabular-nums text-ink-gray-9"
					style="line-height: 1"
				>
					{{ row.lead.day }}
				</span>
			</div>

			<div class="min-w-0 flex-1">
				<div class="truncate text-base text-ink-gray-8">{{ row.title }}</div>
				<div v-if="row.subtitle" class="mt-0.5 truncate text-sm text-ink-gray-5">
					{{ row.subtitle }}
				</div>
			</div>

			<span
				v-if="row.trailing"
				class="flex shrink-0 items-center gap-1.5 text-sm tabular-nums"
				:class="row.urgent ? 'text-ink-amber-6' : 'text-ink-gray-5'"
			>
				<span
					v-if="row.trailingIcon"
					:class="[row.trailingIcon, 'size-3.5 text-ink-gray-5']"
					aria-hidden="true"
				/>
				{{ row.trailing }}
			</span>
		</component>
	</div>
</template>

<script setup lang="ts">
// rows lead with an avatar, an icon or a date tile; dividers hide around the hovered row
import { RouterLink, type RouteLocationRaw } from "vue-router";
import { Avatar } from "frappe-ui";

type Lead =
	| { kind: "person"; name: string; image?: string | null }
	| { kind: "icon"; icon: string }
	| { kind: "date"; month: string; day: string; muted?: boolean };

type Row = {
	key: string;
	lead: Lead;
	title: string;
	subtitle?: string;
	trailing?: string;
	trailingIcon?: string;
	urgent?: boolean;
	route?: RouteLocationRaw;
};

withDefaults(defineProps<{ rows?: Row[] }>(), { rows: () => [] });

const ROW_STATIC =
	"relative flex items-center gap-3 rounded-4 px-3 py-2.5 before:pointer-events-none before:absolute before:inset-x-3 before:-top-px before:border-t before:border-outline-gray-1 first:before:hidden";

const ROW = `${ROW_STATIC} w-full cursor-pointer text-left transition-colors hover:bg-surface-gray-1 hover:before:opacity-0 [&:hover+*]:before:opacity-0`;
</script>
