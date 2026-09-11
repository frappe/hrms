<template>
	<!--
		A fixed-width nav panel: no collapse, so no rail and no toggle. v1's
		Sidebar is a bare frame, so the gutter and the scroll region are composed
		here rather than supplied by the component.
	-->
	<Sidebar disable-collapse>
		<!--
			A plain identity row, not SidebarHeader: that component is the app
			switcher, and there is nothing to switch to. h-12 keeps it lined up
			with PageHeader the way SidebarHeader would have.
		-->
		<div class="flex h-12 shrink-0 items-center gap-2 px-3">
			<div
				class="grid size-7 shrink-0 place-items-center overflow-hidden rounded-4 bg-surface-gray-7 text-xs font-medium text-ink-white"
			>
				HR
			</div>
			<div class="min-w-0 leading-tight">
				<div class="truncate text-base text-ink-gray-8">Frappe HR</div>
				<div class="truncate text-sm text-ink-gray-5">{{ company }}</div>
			</div>
		</div>

		<!-- SidebarItem carries no horizontal inset, so the gutter is the
		     scroll container's job -->
		<ScrollArea class="min-h-0 flex-1" viewport-class="px-2 pb-4">
			<nav aria-label="Portal">
				<template v-for="section in sections" :key="section.group">
					<SidebarLabel>{{ section.group }}</SidebarLabel>
					<div class="space-y-0.5">
						<SidebarItem
							v-for="item in section.items"
							:key="item.to"
							:label="item.label"
							:icon="item.icon"
							:to="item.to"
							:active="isActive(item.to)"
							:suffix="count(item) ? String(count(item)) : undefined"
							@click="$emit('navigate')"
						/>
					</div>
				</template>
			</nav>
		</ScrollArea>

		<!-- who you are, and the account actions that belong with it -->
		<div class="mt-auto px-2 pb-2">
			<Dropdown :options="accountMenu" match-trigger-width placement="top">
				<SidebarItem :label="employee?.employee_name || '—'" :suffix="role">
					<template #prefix>
						<Avatar
							:label="employee?.employee_name"
							:image="employee?.image"
							size="md"
						/>
					</template>
				</SidebarItem>
			</Dropdown>
		</div>
	</Sidebar>
</template>

<script setup>
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { Avatar, Dropdown, ScrollArea, Sidebar, SidebarItem, SidebarLabel } from "frappe-ui";

import { NAV } from "@/nav";
import { session } from "@/data/session";
import { bootstrap } from "@/data/portal";

const emit = defineEmits(["navigate"]);

const route = useRoute();
const router = useRouter();
const employee = computed(() => bootstrap.data?.employee);
const company = computed(() => employee.value?.company || "");
const role = computed(() => employee.value?.designation || "Employee");
const counts = computed(() => bootstrap.data?.counts || {});

/**
 * Regional and custom apps contribute nav entries through the portal extension
 * hook. They merge into whichever group they name, so an added screen sits with
 * its peers rather than in a second-class list at the bottom.
 */
const sections = computed(() => {
	const extras = bootstrap.data?.extensions || [];
	return NAV.map((section) => ({
		...section,
		items: [...section.items, ...extras.filter((e) => e.group === section.group)],
	}));
});

const accountMenu = [
	{
		label: "My Profile",
		icon: "lucide-user",
		onClick: () => {
			router.push("/me");
			emit("navigate");
		},
	},
	{ label: "Log Out", icon: "lucide-log-out", onClick: () => session.logout.submit() },
];

/**
 * Active state is passed explicitly rather than left to SidebarItem's inference,
 * which matches on route NAME when the target has one. Every extension screen
 * resolves to the same named route (/x/:slug), so inference lights all of them
 * at once; a detail page like /payslips/:name conversely lights none. Matching
 * on the path prefix gets both right.
 */
function isActive(to) {
	return route.path === to || route.path.startsWith(to + "/");
}

function count(item) {
	return item.countKey ? counts.value[item.countKey] || 0 : 0;
}
</script>
