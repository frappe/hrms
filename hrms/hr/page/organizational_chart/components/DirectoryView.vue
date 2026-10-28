<script setup>
import { computed, ref } from "vue";
import { Avatar, Badge, Button, LoadingIndicator, Select, TextInput } from "frappe-ui";
import { leave_label } from "../utils.js";

const props = defineProps({
	people: { type: Array, default: null },
	me: { type: String, default: null },
	companies: { type: Array, default: () => [] },
});
const company = defineModel("company", { type: String });
const frappe = window.frappe;
const __ = window.__;

const query = ref("");
// "" is the "All" option, which the sketch shows as picked from the start
const department = ref("");
const branch = ref("");
// one of the chips: "on_leave", "celebrating", "new_joiners" or "my_team"
const chip = ref(null);

const people = computed(() => props.people || []);

const options_of = (field, all_label) => [
	{ label: all_label, value: "" },
	...[...new Set(people.value.map((person) => person[field]).filter(Boolean))]
		.sort()
		.map((value) => ({ label: value, value })),
];
const departments = computed(() => options_of("department", __("All departments")));
const branches = computed(() => options_of("branch", __("All offices")));

// a manager's team is their reports, anyone else's the people who share their manager
const my_team = computed(() => {
	const reports = people.value.filter((person) => person.manager === props.me);
	if (reports.length) return new Set(reports.map((person) => person.id));
	const manager = people.value.find((person) => person.id === props.me)?.manager;
	if (!manager) return new Set();
	return new Set(
		people.value.filter((person) => person.manager === manager).map((person) => person.id),
	);
});

const chips = computed(() =>
	[
		{
			value: "on_leave",
			label: __("On leave"),
			icon: "lucide-tree-palm",
			matches: (person) => Boolean(person.leave),
		},
		{
			value: "celebrating",
			label: __("Celebrating"),
			icon: "lucide-cake",
			matches: (person) => Boolean(person.celebrating),
		},
		{
			value: "new_joiners",
			label: __("New joiners"),
			icon: "lucide-sparkle",
			matches: (person) => person.new_joiner,
		},
		{
			value: "my_team",
			label: __("My team"),
			icon: "lucide-users",
			matches: (person) => my_team.value.has(person.id),
		},
	]
		.map((option) => ({ ...option, count: people.value.filter(option.matches).length }))
		.filter((option) => option.count),
);

const shown = computed(() => {
	const text = query.value.trim().toLowerCase();
	const chip_matches = chips.value.find((option) => option.value === chip.value)?.matches;
	return people.value.filter(
		(person) =>
			(!text ||
				[
					person.name,
					person.id,
					person.designation,
					person.department,
					person.branch,
				].some((value) => value?.toLowerCase().includes(text))) &&
			(!department.value || person.department === department.value) &&
			(!branch.value || person.branch === branch.value) &&
			(!chip_matches || chip_matches(person)),
	);
});

// by department, each in chart order so its head comes first
const groups = computed(() => {
	const by_department = new Map();
	for (const person of shown.value) {
		const name = person.department || "";
		if (!by_department.has(name)) by_department.set(name, []);
		by_department.get(name).push(person);
	}
	return [...by_department]
		.sort(([a], [b]) => (!a ? 1 : !b ? -1 : a.localeCompare(b)))
		.map(([name, members]) => ({ name: name || __("No department"), members }));
});

const count_text = computed(() =>
	shown.value.length === 1 ? __("1 person") : __("{0} people", [shown.value.length]),
);

const filtered = computed(() =>
	Boolean(query.value.trim() || department.value || branch.value || chip.value),
);

function clear_filters() {
	query.value = "";
	department.value = "";
	branch.value = "";
	chip.value = null;
}

// the Employee form, until the profile page replaces it
function open_profile(person) {
	if (person.can_open) frappe.set_route("Form", "Employee", person.id);
}

function celebration_label({ birthday, years }) {
	if (birthday) return __("Birthday today");
	return years === 1 ? __("1 year today") : __("{0} years today", [years]);
}

function toggle_chip(value) {
	chip.value = chip.value === value ? null : value;
}
</script>

<template>
	<div class="h-full overflow-y-auto">
		<div class="mx-auto max-w-3xl px-4 pb-6 pt-4">
			<div class="flex flex-col gap-3">
				<div class="flex items-center justify-between gap-3">
					<span class="text-base tabular-nums text-ink-gray-6">{{ count_text }}</span>
					<slot name="switch" />
				</div>
				<div class="flex flex-wrap items-center gap-2">
					<TextInput
						v-model="query"
						type="search"
						class="w-full sm:w-auto sm:min-w-48 sm:flex-1"
						:placeholder="__('Search name, role or office')"
					>
						<template #prefix>
							<span
								class="lucide-search size-4 text-ink-gray-5"
								aria-hidden="true"
							/>
						</template>
					</TextInput>
					<Select
						v-model="department"
						:options="departments"
						class="min-w-0 flex-1 sm:w-40 sm:flex-none"
					>
						<template #trigger="{ selectedOption }">
							<span class="flex min-w-0 flex-1 items-center gap-2">
								<span
									class="lucide-building-2 size-4 shrink-0"
									aria-hidden="true"
								/>
								<span class="truncate">
									{{
										selectedOption?.value
											? selectedOption.label
											: __("Department")
									}}
								</span>
							</span>
							<span
								class="lucide-chevron-down size-4 shrink-0 text-ink-gray-5"
								aria-hidden="true"
							/>
						</template>
					</Select>
					<Select
						v-model="branch"
						:options="branches"
						class="min-w-0 flex-1 sm:w-32 sm:flex-none"
					>
						<template #trigger="{ selectedOption }">
							<span class="flex min-w-0 flex-1 items-center gap-2">
								<span class="lucide-map-pin size-4 shrink-0" aria-hidden="true" />
								<span class="truncate">
									{{
										selectedOption?.value ? selectedOption.label : __("Office")
									}}
								</span>
							</span>
							<span
								class="lucide-chevron-down size-4 shrink-0 text-ink-gray-5"
								aria-hidden="true"
							/>
						</template>
					</Select>
					<Select
						v-if="companies.length > 1"
						v-model="company"
						:options="companies"
						class="min-w-0 flex-1 sm:w-40 sm:flex-none"
					/>
				</div>

				<div class="flex flex-wrap items-center gap-2">
					<Button
						v-for="option in chips"
						:key="option.value"
						:variant="chip === option.value ? 'subtle' : 'outline'"
						:aria-pressed="chip === option.value"
						@click="toggle_chip(option.value)"
					>
						<template #prefix>
							<span :class="option.icon" class="size-4" aria-hidden="true" />
						</template>
						{{ option.label }}
						<span class="tabular-nums text-ink-gray-5">{{ option.count }}</span>
					</Button>
					<Button
						v-if="filtered"
						variant="ghost"
						:label="__('Clear')"
						@click="clear_filters"
					/>
				</div>
			</div>

			<div v-if="!props.people" class="flex justify-center py-16">
				<LoadingIndicator class="size-5 text-ink-gray-5" />
			</div>

			<p v-else-if="!shown.length" class="py-16 text-center text-base text-ink-gray-6">
				{{ __("No one found") }}
			</p>

			<div v-else>
				<section v-for="group in groups" :key="group.name" class="mt-4">
					<div class="sticky top-0 z-10 flex h-10 items-center gap-2 bg-surface-base">
						<h2 class="text-base-semibold text-ink-gray-9">{{ group.name }}</h2>
						<span class="text-base tabular-nums text-ink-gray-5">
							{{ group.members.length }}
						</span>
					</div>
					<div class="flex flex-col gap-px rounded-6 border border-outline-gray-1 p-1">
						<!-- only a profile the user may open is a button -->
						<component
							:is="person.can_open ? 'button' : 'div'"
							v-for="person in group.members"
							:key="person.id"
							:type="person.can_open ? 'button' : undefined"
							class="relative flex w-full items-center gap-3 rounded-4 px-3 py-2.5 text-left transition-colors before:pointer-events-none before:absolute before:inset-x-3 before:-top-px before:border-t before:border-outline-gray-1 first:before:hidden"
							:class="
								person.can_open &&
								'cursor-pointer hover:bg-surface-gray-1 hover:before:opacity-0 [&:hover+*]:before:opacity-0'
							"
							@click="open_profile(person)"
						>
							<Avatar :image="person.image" :label="person.name" size="xl" />
							<span class="min-w-0 flex-1">
								<span class="flex items-center gap-2">
									<span class="truncate text-base text-ink-gray-8">{{
										person.name
									}}</span>
									<span
										v-if="person.id === me"
										class="shrink-0 text-sm text-ink-gray-5"
									>
										{{ __("You") }}
									</span>
								</span>
								<span class="mt-0.5 block truncate text-sm text-ink-gray-5">
									{{ person.designation }}
								</span>
							</span>
							<span
								class="hidden w-32 shrink-0 items-center gap-1.5 text-base text-ink-gray-6 sm:flex"
							>
								<template v-if="person.branch">
									<span class="lucide-map-pin size-4 shrink-0 text-ink-gray-5" />
									<span class="truncate">{{ person.branch }}</span>
								</template>
							</span>
							<span class="flex shrink-0 justify-end sm:w-36">
								<Badge
									v-if="person.leave"
									theme="blue"
									:label="leave_label(person.leave)"
								>
									<template #prefix>
										<span class="lucide-tree-palm size-3" aria-hidden="true" />
									</template>
								</Badge>
								<Badge
									v-else-if="person.celebrating"
									theme="gray"
									:label="celebration_label(person.celebrating)"
								>
									<template #prefix>
										<span
											:class="
												person.celebrating.birthday
													? 'lucide-cake'
													: 'lucide-party-popper'
											"
											class="size-3"
											aria-hidden="true"
										/>
									</template>
								</Badge>
								<Badge
									v-else-if="person.new_joiner"
									theme="gray"
									:label="__('New joiner')"
								>
									<template #prefix>
										<span class="lucide-sparkle size-3" aria-hidden="true" />
									</template>
								</Badge>
							</span>
						</component>
					</div>
				</section>
			</div>
		</div>
	</div>
</template>
