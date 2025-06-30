<template>
	<div v-if="user.data" class="min-h-screen">
		<NavBar :user="user.data" />
		<MonthView />
		<Toasts />
	</div>
</template>

<script setup lang="ts">
import { Toasts, createResource } from "frappe-ui";

import NavBar from "../components/NavBar.vue";
import MonthView from "./MonthView.vue";

export type User = {
	[K in "name" | "first_name" | "full_name" | "user_image"]: string;
} & {
	roles: string[];
};

// RESOURCES

const user = createResource({
	url: "hrms.api.get_current_user_info",
	auto: true,
	onError() {
		window.location.href = "/login?redirect-to=%2Fhr%2Froster";
	},
});
</script>
