<template>
	<!-- FrappeUIProvider replaces <Toasts /> from 0.1.278: it hosts the toast portal -->
	<FrappeUIProvider>
		<div class="flex h-[100dvh] overflow-hidden bg-surface-white">
			<!-- one instance: the sidebar collapses itself to a rail below lg -->
			<div class="hidden h-full md:block"><AppSidebar /></div>

			<div class="flex min-w-0 flex-1 flex-col">
				<main class="flex-1 overflow-y-auto overflow-x-hidden">
					<div v-if="bootstrap.loading && !bootstrap.data" class="p-6">
						<LoadingIndicator class="h-5 w-5 text-ink-gray-5" />
					</div>

					<div
						v-else-if="bootstrap.data && !bootstrap.data.employee"
						class="mx-auto max-w-md p-6 text-center"
					>
						<h1 class="text-lg font-semibold text-ink-gray-9">No employee record</h1>
						<p class="mt-2 text-p-base text-ink-gray-6">
							This portal shows your own HR record, and
							<span class="font-medium text-ink-gray-8">{{ session.user }}</span>
							is not linked to one yet. Ask HR to set the User field on your Employee
							record.
						</p>
					</div>

					<RouterView v-else />
				</main>

				<BottomTabs class="md:hidden" @more="drawer = true" />
			</div>

			<!-- off-canvas navigation below md -->
			<Transition
				enter-active-class="transition-opacity duration-150"
				leave-active-class="transition-opacity duration-150"
				enter-from-class="opacity-0"
				leave-to-class="opacity-0"
			>
				<div
					v-if="drawer"
					class="fixed inset-0 z-40 bg-black/40 md:hidden"
					@click="drawer = false"
				/>
			</Transition>
			<Transition
				enter-active-class="transition-transform duration-200"
				leave-active-class="transition-transform duration-200"
				enter-from-class="-translate-x-full"
				leave-to-class="-translate-x-full"
			>
				<div v-if="drawer" class="fixed inset-y-0 left-0 z-50 md:hidden">
					<AppSidebar expanded @navigate="drawer = false" />
				</div>
			</Transition>
		</div>
		<Dialogs />
	</FrappeUIProvider>
</template>

<script setup>
import { ref, watch } from "vue";
import { useRoute } from "vue-router";
import { Dialogs, FrappeUIProvider, LoadingIndicator } from "frappe-ui";

import AppSidebar from "@/components/AppSidebar.vue";
import BottomTabs from "@/components/BottomTabs.vue";

import { bootstrap } from "@/data/portal";
import { session } from "@/data/session";
import { setCurrency } from "@/utils/format";

const drawer = ref(false);
const route = useRoute();

watch(
	() => route.fullPath,
	() => (drawer.value = false),
);
watch(
	() => bootstrap.data?.currency,
	(value) => setCurrency(value),
	{ immediate: true },
);
</script>
