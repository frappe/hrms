<script setup lang="ts">
// The company directory: everyone, grouped by department, with search and the filters that
// answer a real question (who is out, who is celebrating, who is on my team).
import { computed, ref } from "vue";
import { Avatar, Button } from "frappe-ui";
import EmptyState from "./EmptyState.vue";
import FilterChip from "./FilterChip.vue";
import FilterMenu from "./FilterMenu.vue";
import MomentBadge from "./MomentBadge.vue";
import SearchField from "./SearchField.vue";
import { BOX, ROW } from "../lib/list";
import { openEmployee } from "../lib/nav";
import {
	DEPT_ORDER,
	OFFICES,
	celebration,
	chainOf,
	deptOf,
	isHead,
	meId,
	momentOf,
	reportsOf,
	staff,
} from "../lib/people";

declare const __: (text: string, args?: unknown[]) => string;

const q = ref("");
const dept = ref("");
const office = ref("");
const outOnly = ref(false);
const celebrating = ref(false);
const myTeam = ref(false);

const outCount = computed(() => staff.value.filter((p) => p.out).length);
const celebratingCount = computed(() => staff.value.filter((p) => celebration(p)).length);
const teamCount = computed(() => (meId.value ? reportsOf(meId.value).length : 0));
const filtered = computed(
	() =>
		!!(
			q.value.trim() ||
			dept.value ||
			office.value ||
			outOnly.value ||
			celebrating.value ||
			myTeam.value
		),
);
const needle = computed(() => q.value.trim().toLowerCase());

const people = computed(() =>
	staff.value.filter((p) => {
		if (dept.value && deptOf(p.id) !== dept.value) return false;
		if (office.value && p.office !== office.value) return false;
		if (outOnly.value && !p.out) return false;
		if (celebrating.value && !celebration(p)) return false;
		if (myTeam.value && p.id !== meId.value && p.manager !== meId.value) return false;
		if (
			needle.value &&
			!`${p.name} ${p.role} ${p.office} ${deptOf(p.id)}`.toLowerCase().includes(needle.value)
		)
			return false;
		return true;
	}),
);

// Your own department first, then the rest alphabetically; heads lead each group.
const groups = computed(() => {
	const mine = deptOf(meId.value);
	const order = [...(mine ? [mine] : []), ...DEPT_ORDER.value.filter((d) => d !== mine)];
	return order
		.map((d) => {
			const rows = people.value
				.filter((p) => deptOf(p.id) === d)
				.sort(
					(a, b) =>
						Number(isHead(b.id)) - Number(isHead(a.id)) ||
						chainOf(a.id).length - chainOf(b.id).length ||
						a.name.localeCompare(b.name),
				)
				.map((p) => ({
					id: p.id,
					name: p.name,
					role: p.role,
					office: p.office,
					photo: p.photo,
					isMe: p.id === meId.value,
					moment: momentOf(p),
				}));
			return { dept: d, count: rows.length, people: rows };
		})
		.filter((g) => g.people.length);
});

const total = computed(() =>
	people.value.length === 1 ? __("1 person") : __("{0} people", [people.value.length]),
);

function clear() {
	q.value = "";
	dept.value = "";
	office.value = "";
	outOnly.value = false;
	celebrating.value = false;
	myTeam.value = false;
}

// A row is a link to the Employee form, so it opens in a new tab with a modifier key.
const formUrl = (id: string) => `/desk/employee/${encodeURIComponent(id)}`;
function open(e: MouseEvent, id: string) {
	if (e.metaKey || e.ctrlKey || e.shiftKey || e.button) return;
	e.preventDefault();
	openEmployee(id);
}
</script>

<template>
	<div>
		<div class="flex flex-col gap-3">
			<div class="flex flex-wrap items-center gap-2">
				<SearchField
					v-model="q"
					:placeholder="__('Search name, role or office')"
					class="min-w-48 flex-1"
				/>
				<FilterMenu
					v-model="dept"
					:label="__('Department')"
					:all-label="__('All departments')"
					icon="lucide-building-2"
					:options="DEPT_ORDER"
				/>
				<FilterMenu
					v-model="office"
					:label="__('Office')"
					:all-label="__('All offices')"
					icon="lucide-map-pin"
					:options="OFFICES"
				/>
			</div>
			<div class="flex flex-wrap items-center gap-2">
				<FilterChip
					:label="__('On leave')"
					icon="lucide-tree-palm"
					:count="outCount"
					:active="outOnly"
					@click="outOnly = !outOnly"
				/>
				<FilterChip
					:label="__('Celebrating')"
					icon="lucide-cake"
					:count="celebratingCount"
					:active="celebrating"
					@click="celebrating = !celebrating"
				/>
				<FilterChip
					v-if="teamCount"
					:label="__('My team')"
					icon="lucide-users"
					:count="teamCount"
					:active="myTeam"
					@click="myTeam = !myTeam"
				/>
				<Button v-if="filtered" variant="ghost" :label="__('Clear')" @click="clear" />
				<p class="ml-auto text-sm tabular-nums text-ink-gray-5 max-md:hidden">
					{{ total }}
				</p>
			</div>
		</div>

		<EmptyState
			v-if="!people.length"
			icon="lucide-search-x"
			:title="__('No one matches')"
			:description="__('Try a different name, or clear the filters.')"
		>
			<Button variant="subtle" :label="__('Clear filters')" @click="clear" />
		</EmptyState>

		<div v-else class="mt-6 flex flex-col gap-6">
			<section v-for="group in groups" :key="group.dept" class="min-w-0">
				<div class="sticky top-0 z-10 flex h-10 items-center gap-2 bg-surface-base">
					<h2 class="text-base font-semibold text-ink-gray-9">{{ group.dept }}</h2>
					<p class="text-base tabular-nums text-ink-gray-5">{{ group.count }}</p>
				</div>
				<div :class="BOX">
					<a
						v-for="row in group.people"
						:key="row.id"
						:href="formUrl(row.id)"
						:class="ROW"
						@click="open($event, row.id)"
					>
						<Avatar :image="row.photo" :label="row.name" size="xl" class="shrink-0" />
						<div class="min-w-0 flex-1">
							<div class="flex items-center gap-2">
								<p class="truncate text-base text-ink-gray-8">{{ row.name }}</p>
								<span v-if="row.isMe" class="shrink-0 text-sm text-ink-gray-5">{{
									__("You")
								}}</span>
							</div>
							<p class="mt-0.5 truncate text-sm text-ink-gray-5">{{ row.role }}</p>
						</div>
						<div class="flex w-32 shrink-0 items-center gap-1.5 max-md:hidden">
							<span
								v-if="row.office"
								class="lucide-map-pin size-4 shrink-0 text-ink-gray-5"
								aria-hidden="true"
							/>
							<p class="truncate text-base text-ink-gray-6">{{ row.office }}</p>
						</div>
						<div class="flex w-36 shrink-0 justify-end max-md:w-auto">
							<MomentBadge :moment="row.moment" />
						</div>
					</a>
				</div>
			</section>
		</div>
	</div>
</template>
