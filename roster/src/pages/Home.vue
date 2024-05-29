<template>
	<div class="bg-gray-50 min-h-screen">
		<NavBar />
		<MonthView />
		<Toasts />
	</div>
</template>

<script setup lang="ts">
import { Toasts } from "frappe-ui";

import NavBar from "../components/NavBar.vue";
import MonthView from "./MonthView.vue";
</script>
