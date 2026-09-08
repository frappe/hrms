<template>
	<PageBody :loading="profileData.loading && !profileData.data">
		<template v-if="d">
			<PageHead title="Profile" subtitle="Your personal and work details" />

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
					<Button variant="solid" @click="edit('personal')">Edit Profile</Button>
				</template>
			</IdentityBand>

			<!--
				Tabs owns the tablist semantics and keyboard navigation that used to be
				hand-rolled here. Its v-model is the tab index; the URL keeps the key,
				so a tab stays linkable and survives a refresh.
			-->
			<Tabs v-model="tabIndex" :tabs="TABS">
				<template #tab-panel="{ tab: t }">
					<!-- ABOUT -->
					<div
						v-if="t.key === 'about'"
						class="grid items-start gap-3.5 pt-3.5 lg:grid-cols-2"
					>
						<div class="flex flex-col gap-3.5">
							<SectionCard title="Personal" action="Edit" @action="edit('personal')">
								<dl class="flex flex-col">
									<FieldRow
										label="Full name"
										:value="d.personal.employee_name"
										locked
									/>
									<FieldRow
										label="Date of birth"
										:value="
											d.personal.date_of_birth
												? date(d.personal.date_of_birth)
												: ''
										"
										locked
									/>
									<FieldRow label="Gender" :value="d.personal.gender" />
									<FieldRow
										label="Blood group"
										:value="d.personal.blood_group"
									/>
									<FieldRow
										label="Marital status"
										:value="d.personal.marital_status"
									/>
								</dl>
							</SectionCard>

							<SectionCard
								title="Addresses"
								action="Edit"
								@action="edit('addresses')"
							>
								<dl class="flex flex-col">
									<FieldRow
										label="Current"
										:value="d.addresses.current_address"
									/>
									<FieldRow
										label="Permanent"
										:value="d.addresses.permanent_address"
									/>
								</dl>
							</SectionCard>
						</div>

						<div class="flex flex-col gap-3.5">
							<SectionCard title="Contact" action="Edit" @action="edit('contact')">
								<dl class="flex flex-col">
									<FieldRow
										label="Work email"
										:value="d.contact.company_email"
										locked
									/>
									<FieldRow
										label="Personal email"
										:value="d.contact.personal_email"
									/>
									<FieldRow label="Mobile" :value="d.contact.cell_number" nums />
								</dl>
							</SectionCard>

							<SectionCard
								title="Emergency Contact"
								:action="hasEmergency ? 'Edit' : 'Add'"
								@action="edit('emergency')"
							>
								<dl v-if="hasEmergency" class="flex flex-col">
									<FieldRow
										label="Name"
										:value="d.emergency.person_to_be_contacted"
									/>
									<FieldRow label="Relation" :value="d.emergency.relation" />
									<FieldRow
										label="Phone"
										:value="d.emergency.emergency_phone_number"
										nums
									/>
								</dl>
								<EmptyState
									v-else
									message="No emergency contact on file."
									action="Add a Contact"
									@action="edit('emergency')"
								/>
							</SectionCard>
						</div>
					</div>

					<!-- JOB -->
					<div
						v-else-if="t.key === 'job'"
						class="grid items-start gap-3.5 pt-3.5 lg:grid-cols-2"
					>
						<div class="flex flex-col gap-3.5">
							<SectionCard title="Position" readonly-label="HR-owned">
								<dl class="flex flex-col">
									<FieldRow
										label="Designation"
										:value="d.position.designation"
										locked
									/>
									<FieldRow
										label="Department"
										:value="d.position.department"
										locked
									/>
									<FieldRow
										label="Employment type"
										:value="d.position.employment_type"
										locked
									/>
									<FieldRow label="Grade" :value="d.position.grade" locked />
									<FieldRow label="Location" :value="d.position.branch" locked />
								</dl>
								<Button
									class="-ml-2 self-start"
									variant="ghost"
									label="Request a change"
									@click="requestChange"
								/>
							</SectionCard>

							<SectionCard title="History" :padded="false">
								<ul class="px-3.5 pb-3.5">
									<li
										v-for="h in d.history"
										:key="h.date + h.label"
										class="flex gap-3 border-b border-outline-gray-1 py-2 last:border-0"
									>
										<span class="nums w-20 shrink-0 text-base text-ink-gray-5">
											{{ h.date ? date(h.date, "MMM YYYY") : "—" }}
										</span>
										<span class="text-p-base text-ink-gray-8">{{
											h.label
										}}</span>
									</li>
								</ul>
							</SectionCard>
						</div>

						<div class="flex flex-col gap-3.5">
							<SectionCard title="Reporting">
								<template #action>
									<Button variant="ghost" route="/org-chart" label="Org chart" />
								</template>
								<div
									v-if="d.reporting.manager || d.reporting.skip"
									class="flex flex-col gap-3"
								>
									<PersonRow
										v-if="d.reporting.manager"
										:name="d.reporting.manager.employee_name"
										:image="d.reporting.manager.image"
										:meta="`${
											d.reporting.manager.designation || ''
										} · Manager`"
										:to="`/directory/${d.reporting.manager.name}`"
										size="2xl"
									/>
									<PersonRow
										v-if="d.reporting.skip"
										:name="d.reporting.skip.employee_name"
										:image="d.reporting.skip.image"
										:meta="`${
											d.reporting.skip.designation || ''
										} · Skip-level`"
										:to="`/directory/${d.reporting.skip.name}`"
										size="2xl"
									/>
								</div>
								<EmptyState v-else message="No reporting manager set." />
							</SectionCard>

							<SectionCard v-if="d.reporting.peers.length" title="Team">
								<template #action>
									<Button variant="ghost" route="/directory" label="Directory" />
								</template>
								<div class="flex flex-wrap items-center gap-1.5">
									<RouterLink
										v-for="p in d.reporting.peers"
										:key="p.name"
										:to="`/directory/${p.name}`"
										:title="p.employee_name"
									>
										<Avatar
											:label="p.employee_name"
											:image="p.image"
											size="lg"
										/>
									</RouterLink>
									<span class="ml-1 text-base text-ink-gray-5">
										{{ d.reporting.peers.length }} peers
									</span>
								</div>
							</SectionCard>
						</div>
					</div>

					<!-- PAY -->
					<div
						v-else-if="t.key === 'pay'"
						class="grid items-start gap-3.5 pt-3.5 lg:grid-cols-2"
					>
						<SectionCard title="Recent Payslips" :padded="false">
							<template #action>
								<Button variant="ghost" route="/payslips" label="View all" />
							</template>
							<DataTable
								:columns="payCols"
								:rows="d.pay.slips"
								empty-message="No payslips issued yet."
							>
								<template #cell-gross_pay="{ row }">{{
									money(row.gross_pay)
								}}</template>
								<template #cell-net_pay="{ row }">
									<span class="font-semibold text-ink-gray-9">{{
										money(row.net_pay)
									}}</span>
								</template>
							</DataTable>
						</SectionCard>

						<div class="flex flex-col gap-3.5">
							<SectionCard title="Bank Account" action="Edit" @action="edit('bank')">
								<dl class="flex flex-col">
									<FieldRow label="Bank" :value="d.pay.bank.bank_name" />
									<FieldRow label="Account" :value="d.pay.bank.account" nums />
									<FieldRow label="IFSC" :value="d.pay.bank.ifsc" />
								</dl>
							</SectionCard>

							<SectionCard title="Tax">
								<template #action>
									<Button variant="ghost" route="/payslips" label="Declare" />
								</template>
								<dl class="flex flex-col">
									<FieldRow
										label="Declared"
										:value="money(d.pay.tax.declared)"
										nums
									/>
									<FieldRow
										label="Status"
										:value="
											d.pay.tax.has_declaration
												? 'Submitted'
												: 'Not declared'
										"
									/>
								</dl>
							</SectionCard>
						</div>
					</div>

					<!-- TIME -->
					<div
						v-else-if="t.key === 'time'"
						class="grid items-start gap-3.5 pt-3.5 lg:grid-cols-2"
					>
						<div class="flex flex-col gap-3.5">
							<SectionCard title="Leave Balance">
								<template #action>
									<Button variant="ghost" route="/leave" label="Open leave" />
								</template>
								<BalanceBars :balances="d.time.balances" />
							</SectionCard>

							<SectionCard title="Upcoming Leave">
								<dl v-if="d.time.upcoming_leave.length" class="flex flex-col">
									<FieldRow
										v-for="l in d.time.upcoming_leave"
										:key="l.from_date + l.leave_type"
										:label="date(l.from_date, 'D MMM')"
										:value="`${l.leave_type}, ${l.total_leave_days} day${
											l.total_leave_days === 1 ? '' : 's'
										} (${l.status})`"
									/>
								</dl>
								<EmptyState v-else message="No leave booked ahead." />
							</SectionCard>
						</div>

						<SectionCard title="Shift and Calendar" readonly-label="HR-owned">
							<dl class="flex flex-col">
								<FieldRow
									label="Assigned shift"
									:value="d.time.shift?.name"
									locked
								/>
								<FieldRow
									label="Timing"
									:value="shiftTiming(d.time.shift)"
									locked
									nums
								/>
								<FieldRow label="Weekly off" :value="d.time.weekly_off" locked />
								<FieldRow
									label="Holiday list"
									:value="d.time.holiday_list"
									locked
								/>
							</dl>
						</SectionCard>
					</div>

					<!-- DOCUMENTS -->
					<div v-else class="grid items-start gap-3.5 pt-3.5 lg:grid-cols-2">
						<SectionCard title="My Documents" :padded="false">
							<DataTable
								:columns="docCols"
								:rows="d.documents"
								clickable
								empty-message="Nothing attached to your employee record yet."
								@row-click="openFile"
							>
								<template #cell-modified="{ row }">{{
									date(row.modified)
								}}</template>
							</DataTable>
						</SectionCard>

						<SectionCard title="From the Company">
							<template #action>
								<Button variant="ghost" route="/documents" label="Open" />
							</template>
							<EmptyState
								message="Company-wide policies and handbooks live under Documents."
							/>
						</SectionCard>
					</div>
				</template>
			</Tabs>

			<EditDialog
				v-model:open="dialogOpen"
				:title="dialog.title"
				:fields="dialog.fields"
				:values="dialogValues"
				@saved="profileData.reload()"
			/>
		</template>
	</PageBody>
</template>

<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { Avatar, Button, Tabs } from "frappe-ui";

import PageBody from "@/components/PageBody.vue";
import PageHead from "@/components/PageHead.vue";
import SectionCard from "@/components/SectionCard.vue";
import IdentityBand from "@/components/IdentityBand.vue";
import DataTable from "@/components/DataTable.vue";
import FieldRow from "@/components/FieldRow.vue";
import PersonRow from "@/components/PersonRow.vue";
import BalanceBars from "@/components/BalanceBars.vue";
import EmptyState from "@/components/EmptyState.vue";
import EditDialog from "@/components/EditDialog.vue";

import { profileData, profileFieldOptions } from "@/data/portal";
import { date, money, shiftTiming } from "@/utils/format";
import { notifyInfo } from "@/utils/toast";

const TABS = [
	{ key: "about", label: "About" },
	{ key: "job", label: "Job" },
	{ key: "pay", label: "Pay" },
	{ key: "time", label: "Time" },
	{ key: "documents", label: "Documents" },
];

const payCols = [
	{ key: "period", label: "Period", primary: true },
	{
		key: "gross_pay",
		label: "Gross",
		align: "right",
		nums: true,
		muted: true,
		hideOnMobile: true,
	},
	{ key: "net_pay", label: "Net Pay", align: "right", nums: true },
];

const docCols = [
	{ key: "file_name", label: "File", primary: true },
	{ key: "modified", label: "Added", nums: true, muted: true, align: "right" },
];

const route = useRoute();
const router = useRouter();

const d = computed(() => profileData.data);
const e = computed(() => d.value?.employee || {});
const opts = computed(() => profileFieldOptions.data || {});

const tab = ref(TABS.some((t) => t.key === route.query.tab) ? route.query.tab : "about");
watch(
	() => route.query.tab,
	(v) => {
		if (v && TABS.some((t) => t.key === v)) tab.value = v;
	},
);

// Tabs models the selected index; the URL and the rest of this page speak in
// keys, so this is the one place the two representations meet.
const tabIndex = computed({
	get: () =>
		Math.max(
			0,
			TABS.findIndex((t) => t.key === tab.value),
		),
	set: (i) => {
		const key = TABS[i]?.key;
		if (!key || key === tab.value) return;
		tab.value = key;
		router.replace({ query: { ...route.query, tab: key } });
	},
});

const meta = computed(() =>
	[e.value.designation, e.value.department, e.value.branch].filter(Boolean).join(" · "),
);

const badges = computed(() =>
	[
		e.value.status && {
			tone: e.value.status === "Active" ? "available" : "inactive",
			label: e.value.status,
		},
		e.value.employment_type && { tone: "gray", label: e.value.employment_type },
		e.value.shift?.name && { tone: "gray", label: e.value.shift.name },
	].filter(Boolean),
);

const facts = computed(() =>
	[
		{ label: "Employee ID", value: e.value.employee_number },
		{ label: "Joined", value: e.value.date_of_joining ? date(e.value.date_of_joining) : null },
		{ label: "Tenure", value: e.value.tenure },
		{ label: "Reports To", value: d.value?.reporting?.manager?.employee_name },
		e.value.grade ? { label: "Grade", value: e.value.grade } : null,
	].filter(Boolean),
);

const hasEmergency = computed(() =>
	Boolean(
		d.value?.emergency?.person_to_be_contacted || d.value?.emergency?.emergency_phone_number,
	),
);

const dialogOpen = ref(false);
const dialogKey = ref("personal");

const SECTIONS = computed(() => ({
	personal: {
		title: "Edit Personal Details",
		fields: [
			{
				fieldname: "gender",
				label: "Gender",
				type: "select",
				options: withBlank(opts.value.gender),
			},
			{
				fieldname: "blood_group",
				label: "Blood group",
				type: "select",
				options: withBlank(opts.value.blood_group),
			},
			{
				fieldname: "marital_status",
				label: "Marital status",
				type: "select",
				options: withBlank(opts.value.marital_status),
			},
			{ fieldname: "employee_name", label: "Full name", locked: true },
			{ fieldname: "date_of_birth", label: "Date of birth", locked: true },
		],
		values: () => d.value?.personal || {},
	},
	contact: {
		title: "Edit Contact Details",
		fields: [
			{ fieldname: "personal_email", label: "Personal email", type: "email" },
			{ fieldname: "cell_number", label: "Mobile", type: "text" },
			{ fieldname: "company_email", label: "Work email", locked: true },
		],
		values: () => d.value?.contact || {},
	},
	addresses: {
		title: "Edit Addresses",
		fields: [
			{
				fieldname: "current_address",
				label: "Current address",
				type: "textarea",
				fullWidth: true,
			},
			{
				fieldname: "permanent_address",
				label: "Permanent address",
				type: "textarea",
				fullWidth: true,
			},
		],
		values: () => d.value?.addresses || {},
	},
	emergency: {
		title: hasEmergency.value ? "Edit Emergency Contact" : "Add Emergency Contact",
		fields: [
			{ fieldname: "person_to_be_contacted", label: "Name", type: "text" },
			{ fieldname: "relation", label: "Relation", type: "text" },
			{
				fieldname: "emergency_phone_number",
				label: "Phone",
				type: "text",
				fullWidth: true,
			},
		],
		values: () => d.value?.emergency || {},
	},
	bank: {
		title: "Edit Bank Account",
		fields: [
			{ fieldname: "bank_name", label: "Bank", type: "text" },
			{ fieldname: "bank_ac_no", label: "Account number", type: "text" },
			{ fieldname: "ifsc_code", label: "IFSC", type: "text", fullWidth: true },
		],
		// the API masks the stored account, so the field starts empty on purpose
		values: () => ({
			bank_name: d.value?.pay?.bank?.bank_name,
			ifsc_code: d.value?.pay?.bank?.ifsc,
		}),
	},
}));

const dialog = computed(() => SECTIONS.value[dialogKey.value] || SECTIONS.value.personal);
const dialogValues = computed(() => dialog.value.values() || {});

function withBlank(list) {
	return ["", ...(list || [])];
}

function edit(key) {
	dialogKey.value = key;
	dialogOpen.value = true;
}

function mail() {
	window.location.href = `mailto:${e.value.company_email}`;
}

function requestChange() {
	notifyInfo(
		"Job details are managed by HR",
		"Ask your HR team to update these. A request workflow is not wired up yet.",
	);
}

function openFile(row) {
	if (row.file_url) window.open(row.file_url, "_blank", "noopener");
}

onMounted(() => {
	profileData.fetch();
	profileFieldOptions.fetch();
});
</script>
