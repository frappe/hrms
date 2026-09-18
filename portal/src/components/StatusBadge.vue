<template>
	<!-- xl is the only size on frappe-ui's scale that carries 14px text, so its
	     px-2 / h-7 padding is what matches the rest of the app -->
	<Badge :theme="theme" :label="label || status" variant="subtle" size="xl" />
</template>

<script setup>
import { computed } from "vue";
import { Badge } from "frappe-ui";

const props = defineProps({ status: String, label: String });

/** One state vocabulary across every doctype, so a colour always means the same thing. */
const THEMES = {
	green: [
		"approved",
		"present",
		"verified",
		"paid",
		"reimbursed",
		"available",
		"deducted",
		"claimed",
		"on shift",
		"work from home",
		"completed",
	],
	amber: [
		"pending",
		"open",
		"in review",
		"scheduled",
		"on leave",
		"half day",
		"unmarked",
		"awaiting",
		"due",
		"not declared",
		"withheld",
	],
	red: ["rejected", "absent", "cancelled", "expiring", "expired", "overdue"],
	blue: ["draft", "repaying", "remote", "unsubmitted", "submitted"],
	gray: ["taken", "settled", "closed", "holiday", "weekly off", "you", "inactive", "past"],
};

const theme = computed(() => {
	const key = String(props.status || "").toLowerCase();
	for (const [name, list] of Object.entries(THEMES)) {
		if (list.includes(key)) return name;
	}
	return "gray";
});
</script>
