<template>
	<!--
		frappe-ui's Sidebar owns the chrome: width, collapse animation, section
		labels, and the tooltips that appear once collapsed. It also ships the
		Collapse toggle, so the rail is real state here rather than two separate
		instances rendered at different breakpoints.
	-->
	<Sidebar
		v-model:collapsed="collapsed"
		:header="{ title: 'Frappe HR', subtitle: company, menuItems: appMenu }"
		:sections="sections"
		:disable-collapse="expanded"
	>
		<template #header-logo>
			<div
				class="flex h-full w-full items-center justify-center bg-surface-gray-7 text-base font-bold text-ink-white"
			>
				HR
			</div>
		</template>

		<!-- who you are, and the way to your own record -->
		<template #footer-items>
			<SidebarItem :label="employee?.employee_name || '—'" :suffix="role" @click="go('/me')">
				<template #icon>
					<Avatar :label="employee?.employee_name" :image="employee?.image" size="md" />
				</template>
			</SidebarItem>
		</template>
	</Sidebar>
</template>

<script setup>
import { computed, h, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { breakpointsTailwind, useBreakpoints } from "@vueuse/core";
import { Avatar, FeatherIcon, Sidebar, SidebarItem } from "frappe-ui";

import { NAV } from "@/nav";
import { session } from "@/data/session";
import { bootstrap } from "@/data/portal";

/**
 * The drawer below md wants labels, never the rail. Sidebar force-collapses
 * under its own `sm` breakpoint, and `collapsed` cannot override that, so
 * `expanded` has to reach it as `disableCollapse` — the one flag that wins.
 */
const props = defineProps({ expanded: Boolean });
const emit = defineEmits(["navigate"]);

const route = useRoute();
const router = useRouter();
const employee = computed(() => bootstrap.data?.employee);
const company = computed(() => employee.value?.company || "");
const role = computed(() => employee.value?.designation || "Employee");
const counts = computed(() => bootstrap.data?.counts || {});

// Below lg there is room for the rail but not the labels. This only seeds the
// state, so the Collapse toggle still wins until the breakpoint next changes.
const breakpoints = useBreakpoints(breakpointsTailwind);
const isDesktop = breakpoints.greaterOrEqual("lg");
const collapsed = ref(props.expanded ? false : !isDesktop.value);
watch(isDesktop, (wide) => {
	if (!props.expanded) collapsed.value = !wide;
});

/**
 * SidebarItem renders a string icon as literal text, so a feather name has to
 * arrive as a component. The functional wrapper forwards the sizing and colour
 * classes the component applies.
 */
function icon(name) {
	return (_, { attrs }) => h(FeatherIcon, { name, ...attrs });
}

function go(to) {
	router.push(to);
	emit("navigate");
}

const sections = computed(() =>
	NAV.map((section) => ({
		label: section.group,
		items: section.items.map((item) => ({
			label: item.label,
			icon: icon(item.icon),
			suffix: count(item) ? String(count(item)) : undefined,
			isActive: isActive(item.to),
			// onClick rather than `to`: SidebarItem navigates with router.replace,
			// which would cost the back button on every section change
			onClick: () => go(item.to),
		})),
	})),
);

const appMenu = [{ label: "Log Out", onClick: () => session.logout.submit() }];

function count(item) {
	return item.countKey ? counts.value[item.countKey] || 0 : 0;
}

function isActive(to) {
	return route.path === to || route.path.startsWith(to + "/");
}
</script>
