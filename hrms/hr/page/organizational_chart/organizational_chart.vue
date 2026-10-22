<script setup>
import { computed, onUnmounted, watch } from "vue";
import { FrappeUIProvider, Spinner } from "frappe-ui";
import DirectoryPage from "./components/DirectoryPage.vue";
import EmptyState from "./components/EmptyState.vue";
import OrgChart from "./components/OrgChart.vue";
import PageBody from "./components/PageBody.vue";
import { goChart, goDirectory } from "./lib/nav";
import { failed, loadPeople, ready, staff } from "./lib/people";

// /desk/organizational-chart             the org chart
// /desk/organizational-chart/directory   the directory
// ?focus=<employee> or ?person=<employee> on the chart opens it on that person.

const props = defineProps({
	route: { type: Array, default: () => [] },
	query: { type: Object, default: () => ({}) },
});

const emit = defineEmits(["title", "actions"]);

const frappe = window.frappe;
const __ = window.__;
const PAGE = "organizational-chart";

const view = computed(() => (props.route[0] === "directory" ? "directory" : "chart"));
const title = computed(() => (view.value === "directory" ? __("Directory") : __("Org chart")));

loadPeople();

// Desk draws one crumb from the title, and sets it again each time the page is shown.
watch(title, (text) => emit("title", text), { immediate: true });

// The switch sits at the right of desk's page head, in desk's own TabButtons.
const switcher = new frappe.ui.TabButtons({
	label: __("View"),
	options: [
		{ label: __("Org chart"), value: "chart" },
		{ label: __("Directory"), value: "directory" },
	],
	value: view.value,
	on_change: (value) => (value === "directory" ? goDirectory() : goChart()),
});
const wrapper = window.$(frappe.pages[PAGE]);
const mountSwitch = () => {
	const actions = frappe.pages[PAGE]?.page?.page_actions;
	if (actions && !actions[0].contains(switcher.el)) actions.prepend(switcher.el);
};
mountSwitch();
wrapper.on("show", mountSwitch);
// the data is read again on each visit, behind what is on screen
wrapper.on("show", () => ready.value && loadPeople(true));
watch(view, (value) => switcher.set_value(value, { silent: true }));

onUnmounted(() => {
	wrapper.off("show", mountSwitch);
	switcher.el.remove();
});
</script>

<template>
	<FrappeUIProvider>
		<Spinner v-if="!ready" class="mx-auto mt-20 w-6 text-ink-gray-5" />
		<EmptyState
			v-else-if="failed && !staff.length"
			icon="lucide-users"
			:title="__('Could not load people')"
			:description="__('Reload the page to try again.')"
		/>
		<EmptyState
			v-else-if="!staff.length"
			icon="lucide-users"
			:title="__('No employees')"
			:description="__('Active employees show up here.')"
		/>
		<div v-else-if="view === 'chart'" class="h-full">
			<OrgChart :focus="query.focus" :person="query.person" />
		</div>
		<PageBody v-else :heading="__('Company directory')" :subtitle="__('Search by name, team or role')">
			<DirectoryPage />
		</PageBody>
	</FrappeUIProvider>
</template>
