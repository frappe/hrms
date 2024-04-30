<template>
	<div class="bg-white rounded-lg border p-4">
		<div class="flex">
			<Button icon="chevron-left" variant="ghost" @click="() => updateMonth(-1)" />
			<span class="px-1 w-20 text-center my-auto">{{ month }} '{{ year }}</span>
			<Button icon="chevron-right" variant="ghost" @click="() => updateMonth(1)" />
		</div>
	</div>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import dayjs from "../utils/dayjs";

const firstOfMonth = ref(dayjs().date(1));
const month = computed(() => {
	return dayjs().month(firstOfMonth.value.$M).format("MMM");
});
const year = computed(() => {
	return dayjs().year(firstOfMonth.value.$y).format("YY");
});

const updateMonth = (change) => {
	firstOfMonth.value = firstOfMonth.value.add(change, "M");
};
</script>
