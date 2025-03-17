<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
const route = frappe
  .get_route()
  .filter((r) => r !== "")
  .slice(1);
import Main from "./Main.vue";
import Real from "./Real.vue";

onMounted(() => {
  console.log(this.$root);
});
</script>
<template>
  <div id="app">
    <div v-if="route.length === 0" />
    <Main v-else-if="route.join().includes('new')" />
    <Real v-else />
  </div>
</template>
