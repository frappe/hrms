<template>
	<div class="bg-gray-50 h-screen">
		<NavBar />
		<div class="px-12 py-6 space-y-6">
			<FilterBar />
			<MonthView />
		</div>
	</div>
</template>

<script setup lang="ts">
import NavBar from "../components/NavBar.vue";
import MonthView from "../components/MonthView.vue";
import FilterBar from "../components/FilterBar.vue";
</script>
