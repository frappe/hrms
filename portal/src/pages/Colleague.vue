<template>
	<PageBody :loading="colleagueData.loading && !colleagueData.data">
		<template v-if="e">
			<PageHead
				:crumbs="[{ label: 'Directory', to: '/directory' }, { label: e.employee_name }]"
			/>

			<IdentityBand
				:name="e.employee_name"
				:image="e.image"
				:meta="meta"
				:badges="badges"
				:facts="facts"
			>
				<template #actions>
					<Button v-if="e.company_email" variant="subtle" @click="mail">Email</Button>
					<Button variant="subtle" @click="$router.push('/org-chart')">Org Chart</Button>
				</template>
			</IdentityBand>

			<div class="grid items-start gap-3.5 lg:grid-cols-2">
				<SectionCard v-if="d.manager" title="Reports To">
					<PersonRow
						:name="d.manager.employee_name"
						:image="d.manager.image"
						:meta="d.manager.designation"
						:to="`/directory/${d.manager.name}`"
						size="2xl"
					/>
				</SectionCard>

				<SectionCard v-if="d.reports.length" title="Team">
					<template #action>
						<span class="text-base text-ink-gray-5">
							{{ d.reports.length }} direct reports
						</span>
					</template>
					<div class="flex flex-wrap gap-1.5">
						<RouterLink
							v-for="r in d.reports"
							:key="r.name"
							:to="`/directory/${r.name}`"
							:title="r.employee_name"
						>
							<Avatar :label="r.employee_name" :image="r.image" size="lg" />
						</RouterLink>
					</div>
				</SectionCard>
			</div>

			<p class="text-base text-ink-gray-5">
				Personal, pay and document sections are not part of a colleague's profile.
			</p>
		</template>
	</PageBody>
</template>

<script setup>
import { computed, onMounted, watch } from "vue";
import { useRoute } from "vue-router";
import { Avatar, Button } from "frappe-ui";

import PageBody from "@/components/PageBody.vue";
import PageHead from "@/components/PageHead.vue";
import SectionCard from "@/components/SectionCard.vue";
import IdentityBand from "@/components/IdentityBand.vue";
import PersonRow from "@/components/PersonRow.vue";

import { colleagueData } from "@/data/portal";
import { date } from "@/utils/format";

const route = useRoute();

const d = computed(() => colleagueData.data);
const e = computed(() => d.value?.employee);

const meta = computed(() =>
	[e.value?.designation, e.value?.department, e.value?.branch].filter(Boolean).join(" · "),
);

const badges = computed(() => {
	const a = d.value?.availability;
	if (!a) return [];
	return [
		{
			tone: a.status === "On leave" ? "on leave" : "available",
			label: a.until ? `On leave until ${date(a.until)}` : a.status,
		},
	];
});

/** Public work facts only. No employee ID, no grade. */
const facts = computed(() => [
	{ label: "Work Email", value: e.value?.company_email },
	{ label: "Joined", value: e.value?.date_of_joining ? date(e.value.date_of_joining) : null },
	{ label: "Tenure", value: e.value?.tenure },
	{ label: "Location", value: e.value?.branch },
]);

function mail() {
	window.location.href = `mailto:${e.value.company_email}`;
}

function load() {
	colleagueData.fetch({ employee: route.params.employee });
}

onMounted(load);
watch(() => route.params.employee, load);
</script>
