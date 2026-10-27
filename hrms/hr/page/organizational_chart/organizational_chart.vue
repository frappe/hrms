<script setup>
import { computed, nextTick, onMounted, provide, reactive, ref, watch } from "vue";
import {
	Button,
	Combobox,
	Divider,
	LoadingIndicator,
	Select,
	TabButtons,
	Tooltip,
	debounce,
} from "frappe-ui";
import { useMediaQuery } from "@vueuse/core";
import ChartCanvas from "./components/ChartCanvas.vue";
import EmployeePopover from "./components/EmployeePopover.vue";
import TreeNode from "./components/TreeNode.vue";

defineProps({
	route: { type: Array, default: () => [] },
	query: { type: Object, default: () => ({}) },
});

const emit = defineEmits(["title", "actions"]);

const frappe = window.frappe;
const __ = window.__;
const API = "hrms.hr.page.organizational_chart.organizational_chart";

const canvas = ref(null);
const companies = ref([]);
const company = ref(null);
const roots = ref([]);
const loading = ref(true);

// loaded cards by id, and the ids of each loaded team by manager
const nodes = reactive({});
const teams = reactive({});
const expanded = reactive(new Set());
const me = ref(null);
// the card whose popover is open
const selected = ref(null);
// only Expand all loads every team
const all_loaded = ref(false);
// `top` is what the search list shows before anything is typed
const search = reactive({ query: "", results: [], top: [], loading: false });

// tree: teams across, columns: each team to the right of its manager, list: teams indented
const VIEWS = [
	{ value: "tree", label: __("Tree"), icon: "lucide-network" },
	{ value: "columns", label: __("Columns"), icon: "lucide-columns-3" },
	{ value: "list", label: __("List"), icon: "lucide-list-tree" },
];
// on a phone the switch shows icons only, and the labels stay as accessible names
const narrow = useMediaQuery("(max-width: 639px)");
const view_options = computed(() =>
	VIEWS.map(({ icon, ...option }) =>
		narrow.value ? { ...option, icon } : { ...option, iconLeft: icon },
	),
);
// remembered separately for phone width and wider screens
const view_key = () => `hrms:organizational_chart:view:${narrow.value ? "phone" : "wide"}`;
const view = ref(read_saved_view());

// phones default to the list. Blocked storage counts as no saved choice.
function read_saved_view() {
	const fallback = narrow.value ? "list" : "tree";
	try {
		const saved = localStorage.getItem(view_key());
		return VIEWS.some((option) => option.value === saved) ? saved : fallback;
	} catch {
		return fallback;
	}
}

// resizing across phone width picks up that width's view
watch(narrow, () => (view.value = read_saved_view()));

// only a pick from the switch is saved, not a view changed by resizing
function choose_view(value) {
	view.value = value;
	try {
		localStorage.setItem(view_key(), value);
	} catch {
		// storage is blocked, so the next visit opens the default view
	}
}

watch(view, async () => {
	await nextTick();
	canvas.value?.show_top();
});

// bumped on every company change, so a reply for the previous company is dropped
let load_id = 0;

function add_nodes(list) {
	for (const node of list) nodes[node.id] = node;
	return list.map((node) => node.id);
}

async function load_chart() {
	const id = ++load_id;
	loading.value = true;
	for (const key of Object.keys(nodes)) delete nodes[key];
	for (const key of Object.keys(teams)) delete teams[key];
	expanded.clear();
	roots.value = [];
	selected.value = null;
	all_loaded.value = false;
	search.top = [];

	// a failed call leaves the chart empty rather than loading forever
	try {
		const list = await frappe.xcall(`${API}.get_children`, { company: company.value });
		if (id !== load_id) return;
		roots.value = add_nodes(list);
		load_top_of_chart();
		// a single person at the top is the head of the company, so open their team
		if (roots.value.length === 1) await open_team(roots.value[0]);
	} finally {
		if (id === load_id) loading.value = false;
	}

	await nextTick();
	canvas.value?.show_top();
}

async function open_team(employee) {
	if (!teams[employee]) {
		const id = load_id;
		const list = await frappe.xcall(`${API}.get_children`, {
			company: company.value,
			parent: employee,
		});
		if (id !== load_id) return;
		teams[employee] = add_nodes(list);
	}
	expanded.add(employee);
}

function toggle(employee) {
	return canvas.value.keep_in_place(canvas.value.find_card(employee), () =>
		expanded.has(employee) ? expanded.delete(employee) : open_team(employee),
	);
}

function select(employee) {
	selected.value = selected.value === employee ? null : employee;
}

// opens every team above `employee`, then centres and selects their card
async function show_employee(employee) {
	const id = load_id;
	const path = await frappe.xcall(`${API}.get_path`, { company: company.value, employee });
	for (const manager of path.slice(0, -1)) await open_team(manager);
	await nextTick();
	// the company changed meanwhile
	if (id !== load_id) return;

	const card = canvas.value.find_card(employee);
	if (!card) {
		frappe.show_alert({
			message: __("This person is not in this chart"),
			indicator: "orange",
		});
		return;
	}
	canvas.value.center(card);
	selected.value = employee;
}

// a manager outside the chart has no card, so open their profile if the user may
function show_manager(manager) {
	if (canvas.value.find_card(manager.id)) show_employee(manager.id);
	else if (manager.can_open) frappe.set_route("Form", "Employee", manager.id);
}

const to_options = (list) =>
	list.map((employee) => ({
		label: employee.employee_name,
		value: employee.name,
		description: employee.department || employee.designation,
	}));

async function load_top_of_chart() {
	const id = load_id;
	const list = await frappe.xcall(`${API}.search_employees`, { company: company.value });
	if (id !== load_id) return;
	search.top = to_options(list);
	if (!search.query) search.results = search.top;
}

const run_search = debounce(async (query) => {
	try {
		const list = await frappe.xcall(`${API}.search_employees`, {
			company: company.value,
			txt: query,
		});
		// ignore a slower reply to an older query
		if (query !== search.query) return;
		search.results = to_options(list);
	} finally {
		if (query === search.query) search.loading = false;
	}
}, 300);

watch(
	() => search.query,
	(query) => {
		search.loading = Boolean(query);
		if (query) run_search(query);
		else search.results = search.top;
	},
);

function pick_result(employee) {
	if (!employee) return;
	search.query = "";
	show_employee(employee);
}

const all_open = computed(
	() =>
		all_loaded.value &&
		Object.values(nodes).every((node) => !node.reports || expanded.has(node.id)),
);

function toggle_all() {
	return all_open.value ? collapse_all() : expand_all();
}

// back to how the chart opens: only the head's team
async function collapse_all() {
	expanded.clear();
	if (roots.value.length === 1) expanded.add(roots.value[0]);
	await nextTick();
	canvas.value.show_top();
}

// saves the open teams only, so Expand all first for the whole company
async function save_image() {
	frappe.dom.freeze(__("Exporting..."));
	try {
		await canvas.value.save_image(`${__("Organizational Chart")} - ${company.value}`);
	} catch (error) {
		console.error(error);
		frappe.msgprint(
			__("The chart could not be exported. Try again, or with fewer teams open."),
		);
	} finally {
		frappe.dom.unfreeze();
	}
}

async function expand_all() {
	const id = load_id;
	let list;
	try {
		list = await frappe.xcall(`${API}.get_all_nodes`, { company: company.value });
	} catch {
		// the server's message is already on screen
		return;
	}
	if (id !== load_id) return;

	all_loaded.value = true;
	add_nodes(list);
	for (const key of Object.keys(teams)) delete teams[key];
	for (const node of list) {
		// a manager outside the chart has no card, so their reports stay at the top
		if (node.manager && nodes[node.manager.id]) {
			(teams[node.manager.id] ||= []).push(node.id);
		}
		if (node.reports) expanded.add(node.id);
	}

	await nextTick();
	canvas.value.fit();
}

provide("org_chart", { nodes, teams, expanded, me, selected, view, toggle, select });

watch(company, load_chart);

onMounted(async () => {
	emit("title", __("Organizational Chart"));
	emit("actions", []);

	try {
		const context = await frappe.xcall(`${API}.get_chart_context`);
		companies.value = context.companies;
		me.value = context.employee;
		company.value = context.company;
	} finally {
		if (!company.value) loading.value = false;
	}
});
</script>

<template>
	<div class="relative h-full min-h-0 w-full">
		<div v-if="loading" class="flex h-full items-center justify-center">
			<LoadingIndicator class="size-5 text-ink-gray-5" />
		</div>

		<div
			v-else-if="!roots.length"
			class="flex h-full flex-col items-center justify-center gap-3"
		>
			<p class="text-base text-ink-gray-6">
				{{
					company ? __("No active employees in {0}", [company]) : __("No company found")
				}}
			</p>
			<Button
				v-if="company"
				:label="__('Add Employee')"
				@click="frappe.new_doc('Employee', { company })"
			/>
		</div>

		<ChartCanvas v-else ref="canvas" :selected="selected" @deselect="selected = null">
			<div class="flex items-start" :class="view === 'tree' ? 'gap-8' : 'flex-col gap-6'">
				<TreeNode v-for="root in roots" :key="root" :id="root" />
			</div>

			<template #popover>
				<EmployeePopover
					v-if="nodes[selected]"
					:node="nodes[selected]"
					:company="company"
					:is_me="selected === me"
					:team_open="expanded.has(selected)"
					@close="selected = null"
					@show_manager="show_manager"
					@toggle_team="toggle(selected)"
				/>
			</template>

			<template #corner>
				<TabButtons
					:model-value="view"
					:options="view_options"
					@update:model-value="choose_view"
				/>
			</template>

			<template #panel>
				<div class="flex flex-col gap-2">
					<Combobox
						:model-value="null"
						v-model:query="search.query"
						:options="search.results"
						:filterable="false"
						:loading="search.loading"
						:placeholder="__('Find a person')"
						:empty-text="search.query ? __('No one found') : __('Type a name')"
						variant="outline"
						@update:model-value="pick_result"
					/>
					<Select
						v-if="companies.length > 1"
						v-model="company"
						:options="companies"
						variant="outline"
						class="w-full"
					/>
				</div>
			</template>

			<template #actions>
				<Tooltip v-if="me" :text="__('Find me')">
					<Button
						variant="ghost"
						icon="lucide-locate-fixed"
						:aria-label="__('Find me')"
						@click="show_employee(me)"
					/>
				</Tooltip>
				<Divider orientation="vertical" class="mx-1 hidden !h-4 sm:block" />
				<Button
					variant="ghost"
					class="hidden sm:inline-flex"
					:icon-left="all_open ? 'lucide-fold-vertical' : 'lucide-unfold-vertical'"
					:label="all_open ? __('Collapse') : __('Expand all')"
					@click="toggle_all"
				/>
				<Tooltip :text="__('Export as image')">
					<Button
						variant="ghost"
						icon="lucide-download"
						:aria-label="__('Export as image')"
						@click="save_image"
					/>
				</Tooltip>
			</template>
		</ChartCanvas>
	</div>
</template>
