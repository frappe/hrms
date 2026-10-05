<template>
	<!-- h-full so it also fits the Studio canvas -->
	<div class="h-full min-h-screen w-full bg-surface-base text-ink-gray-8">
		<DesktopShell>
			<template #sidebar>
				<!-- a class on Sidebar is dropped in the build (its template starts with a comment) -->
				<div class="flex h-full [&>[data-slot=sidebar]]:border-r">
					<Sidebar v-model:collapsed="collapsed" width="15rem">
						<SidebarHeader :title="__('Frappe HR')" :menu-items="headerMenu" />

						<div class="px-2 pt-1">
							<SidebarItem
								:label="__('Search')"
								icon="lucide-search"
								@click="searchOpen = true"
							>
								<template #suffix>
									<span class="pr-2 text-sm text-ink-gray-4">{{
										searchHint
									}}</span>
								</template>
							</SidebarItem>
						</div>

						<div class="min-h-0 flex-1 overflow-y-auto px-2 pb-4">
							<SidebarSection
								v-for="(group, index) in navGroups"
								:key="group.label ?? index"
								:label="group.label"
							>
								<SidebarItem
									v-for="item in group.items"
									:key="item.route"
									:label="item.label"
									:icon="item.icon"
									:route="item.route"
									:active="item.route === activeRoute"
								>
									<template v-if="item.badge" #suffix>
										<span class="pr-2 text-sm tabular-nums text-ink-gray-5">{{
											item.badge
										}}</span>
									</template>
								</SidebarItem>
							</SidebarSection>
						</div>

						<div class="px-2 pb-1">
							<SidebarCollapseToggle />
						</div>

						<div class="border-t border-outline-gray-1 p-2">
							<Dropdown :options="userMenu" side="top" align="start">
								<template #default="triggerProps">
									<button
										v-bind="triggerProps"
										type="button"
										class="flex h-10 w-full items-center gap-2 overflow-hidden rounded-4 px-1 text-left transition-colors"
										:aria-label="collapsed ? displayName : undefined"
										:class="
											activeRoute === ROUTES.profile
												? 'bg-surface-elevation-3 shadow-sm'
												: 'hover:bg-surface-gray-2'
										"
									>
										<Avatar
											:image="photo"
											:label="displayName"
											size="md"
											class="shrink-0"
										/>
										<span
											class="min-w-0 flex-1 transition-opacity duration-300"
											:class="collapsed && 'opacity-0'"
										>
											<span class="block truncate text-sm text-ink-gray-8">{{
												displayName
											}}</span>
											<span class="block truncate text-xs text-ink-gray-5">{{
												employee?.company
											}}</span>
										</span>
										<span
											class="lucide-chevrons-up-down size-3.5 shrink-0 text-ink-gray-5"
											aria-hidden="true"
										/>
									</button>
								</template>
							</Dropdown>
						</div>
					</Sidebar>
				</div>
			</template>
			<slot />
		</DesktopShell>
		<PortalSearch v-model:open="searchOpen" />
	</div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { useRoute } from "vue-router";
import {
	Avatar,
	DesktopShell,
	Dropdown,
	Sidebar,
	SidebarCollapseToggle,
	SidebarHeader,
	SidebarItem,
	SidebarSection,
	call,
	useColorScheme,
} from "frappe-ui";
import { useNav } from "@app/nav";
import { ROUTES } from "@app/routes";
import { useSession } from "@app/stores/session";
import { useMediaQuery } from "@app/utils/browser";
import { __ } from "@app/utils/translation";
import PortalSearch from "@app/components/PortalSearch.vue";

const route = useRoute();
const { employee, displayName, photo } = useSession();
const { navGroups, navItems } = useNav();
const { resolvedColorScheme, toggleColorScheme } = useColorScheme();

const searchOpen = ref(false);
const searchHint = navigator.platform.toLowerCase().includes("mac") ? "⌘K" : "Ctrl+K";

// longest matching route, so /onboarding/joiners/x lights Onboarding, not Your first month
const activeRoute = computed(() => {
	const path = route.path;
	const hits = [...navItems.value.map((item) => item.route), ROUTES.profile].filter(
		(itemRoute) =>
			itemRoute === ROUTES.home
				? path === itemRoute
				: path === itemRoute || path.startsWith(`${itemRoute}/`),
	);
	return hits.sort((a, b) => b.length - a.length)[0] ?? "";
});

// fold to icons when the page doesn't fit beside the sidebar; a manual toggle is remembered
const SIDEBAR_FOLD = "(min-width: 768px) and (max-width: 1055px)";
const STORAGE_KEY = "hr.sidebar.collapsed";
const squeezed = useMediaQuery(SIDEBAR_FOLD);
const preference = ref(readPreference());
const heldOpen = ref(false);
const collapsed = computed({
	get: () => preference.value || (squeezed.value && !heldOpen.value),
	set: (value: boolean) => {
		if (squeezed.value) heldOpen.value = !value;
		preference.value = squeezed.value ? false : value;
		writePreference(preference.value);
	},
});

const headerMenu = computed(() => [
	resolvedColorScheme.value === "dark"
		? { label: __("Light theme"), icon: "lucide-sun", onClick: toggleColorScheme }
		: { label: __("Dark theme"), icon: "lucide-moon", onClick: toggleColorScheme },
	{ label: __("Log out"), icon: "lucide-log-out", onClick: logOut },
]);

const userMenu = [{ label: __("My profile"), icon: "lucide-user", route: ROUTES.profile }];

// logout only accepts POST
async function logOut() {
	await call("logout");
	window.location.href = "/login";
}

function readPreference() {
	try {
		return localStorage.getItem(STORAGE_KEY) === "1";
	} catch {
		return false;
	}
}

function writePreference(value: boolean) {
	try {
		localStorage.setItem(STORAGE_KEY, value ? "1" : "0");
	} catch {
		// storage can be blocked in private windows
	}
}
</script>
