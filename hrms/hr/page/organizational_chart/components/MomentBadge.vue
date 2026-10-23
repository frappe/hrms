<script setup lang="ts">
// The one thing about a person that is true now: out, a birthday or anniversary this week, new hire.
// Out is a status (blue, it changes whether you can reach them). The rest are gray facts.
// Pass an employee `id`, or a ready-made `moment` (the directory rows already carry theirs).
import { computed } from "vue";
import { Badge } from "frappe-ui";
import { byId, momentOf } from "../lib/people";
import type { Moment } from "../lib/people";

const props = defineProps<{ id?: string; moment?: Moment | null }>();
const m = computed(() => props.moment ?? (props.id ? momentOf(byId.value[props.id]) : null));
const icon = computed(() => m.value?.icon ?? (m.value?.kind === "out" ? "lucide-tree-palm" : ""));
</script>

<template>
	<Badge v-if="m" :label="m.label" :theme="m.kind === 'out' ? 'blue' : 'gray'" variant="subtle">
		<template #prefix><span :class="[icon, 'size-3']" aria-hidden="true" /></template>
	</Badge>
</template>
