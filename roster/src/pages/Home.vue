<template>
	<div class="bg-gray-50 h-screen">
		<Navbar />
		<div class="p-12">
			<MonthView />
		</div>
	</div>
</template>

<script setup>
import Navbar from "../components/Navbar.vue";
import MonthView from "../components/MonthView.vue";
</script>
