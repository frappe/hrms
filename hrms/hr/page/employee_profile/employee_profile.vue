<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { Badge, Button, FileUploader, LoadingIndicator, Select } from "frappe-ui";
import { leave_label } from "../organizational_chart/utils.js";
import DetailCard from "./components/DetailCard.vue";
import AssetsSection from "./components/AssetsSection.vue";
import BankSection from "./components/BankSection.vue";
import CardEditor from "./components/CardEditor.vue";
import DocumentsSection from "./components/DocumentsSection.vue";
import ProfileCard from "./components/ProfileCard.vue";
import PublicProfile from "./components/PublicProfile.vue";
import { API } from "./utils.js";

const props = defineProps({
	route: { type: Array, default: () => [] },
	query: { type: Object, default: () => ({}) },
	// In the Employee form's Profile tab, the Vue Component field passes the document
	doctype: { type: String, default: null },
	name: { type: String, default: null },
	read_only: { type: Boolean, default: true },
});
const emit = defineEmits(["title", "actions"]);

const frappe = window.frappe;
const __ = window.__;

const in_form = computed(() => props.doctype === "Employee");
// the form's employee in the tab, /employee-profile/HR-EMP-00030 on the page, and on
// /employee-profile alone the user's own
const employee = computed(() => (in_form.value ? props.name : props.route[0]) || null);

const profile = ref(null);
const error = ref(null);
const active = ref("public");
// ‹ › in the form switches records faster than a profile loads, so only the last load is shown
let last_load = 0;

// The open section is kept in the URL, as the form keeps its tab, so a reload opens it again
const url_section = () => new URL(window.location.href).searchParams.get("section");

watch(active, (section) => {
	const url = new URL(window.location.href);
	if (section === "public") url.searchParams.delete("section");
	else url.searchParams.set("section", section);
	if (url.href !== window.location.href) history.replaceState(history.state, "", url);
});

async function load() {
	const this_load = ++last_load;
	const section = url_section();
	profile.value = null;
	error.value = null;
	active.value = "public";
	editing_employment.value = false;
	personal_edit.value = { card: null, values: null };
	let data;
	try {
		data = await frappe.xcall(`${API}.get_profile`, { employee: employee.value });
	} catch (e) {
		if (this_load === last_load) {
			error.value = e?.messages?.[0] || __("You do not have access to this profile");
		}
		return;
	}
	if (this_load !== last_load) return;
	profile.value = data;
	if (data.private && SECTIONS.value.some((item) => item.value === section)) {
		active.value = section;
	}
	if (!in_form.value) {
		emit("title", profile.value.card.name);
		emit(
			"actions",
			profile.value.can_open_record
				? [
						{
							label: __("Open Employee record"),
							onClick: () =>
								frappe.set_route("Form", "Employee", profile.value.card.id),
						},
				  ]
				: [],
		);
	}
}

watch(employee, load);
onMounted(load);

// the private sections, each with what needs attention there as its count
const SECTIONS = computed(() => {
	const data = profile.value?.private;
	const due = data?.documents.filter((doc) =>
		["Missing", "Pending", "Rejected"].includes(doc.status),
	).length;
	return [
		{ value: "personal", label: __("Personal"), icon: "lucide-contact" },
		{
			value: "bank",
			label: __("Bank account"),
			icon: "lucide-landmark",
			count: data?.bank_request ? 1 : 0,
		},
		{ value: "documents", label: __("Documents"), icon: "lucide-file-text", count: due },
		{
			value: "assets",
			label: __("Assets"),
			icon: "lucide-laptop",
			count: data?.assets.length,
		},
		{ value: "employment", label: __("Employment"), icon: "lucide-briefcase-business" },
	];
});

// On a phone the sections are a picker, not a second row of tabs under the Employee form's own
const SECTION_OPTIONS = computed(() => [
	{ value: "public", label: __("Public profile"), icon: "lucide-user-round" },
	...SECTIONS.value.map(({ value, label, icon, count }) => ({
		value,
		label,
		icon,
		description: count ? COUNT_TEXT[value](count) : undefined,
	})),
]);
const COUNT_TEXT = {
	bank: () => __("1 open request"),
	documents: (count) => __("{0} due", [count]),
	assets: (count) => __("{0} assigned", [count]),
};

const format_date = (value) => (value ? frappe.datetime.str_to_user(value) : null);

const personal_rows = computed(() => {
	const personal = profile.value.private.personal;
	return [
		{
			label: __("Date of birth"),
			icon: "lucide-cake",
			value: format_date(personal.date_of_birth),
		},
		{ label: __("Gender"), icon: "lucide-user-round", value: personal.gender },
		{ label: __("Blood group"), icon: "lucide-droplet", value: personal.blood_group },
		{ label: __("Marital status"), icon: "lucide-heart", value: personal.marital_status },
	];
});
const contact_rows = computed(() => {
	const contact = profile.value.private.contact;
	return [
		{ label: __("Mobile"), icon: "lucide-phone", value: contact.cell_number },
		{ label: __("Personal email"), icon: "lucide-mail", value: contact.personal_email },
		{ label: __("Current address"), icon: "lucide-house", value: contact.current_address },
		{
			label: __("Permanent address"),
			icon: "lucide-map-pinned",
			value:
				contact.permanent_address && contact.permanent_address === contact.current_address
					? __("Same as current address")
					: contact.permanent_address,
		},
	];
});
const emergency = computed(() => profile.value.private.emergency);
const employment_rows = computed(() => {
	const employment = profile.value.private.employment;
	const card = profile.value.card;
	return [
		{ label: __("Employee ID"), icon: "lucide-id-card", value: card.id },
		{ label: __("Department"), icon: "lucide-building-2", value: card.department },
		{ label: __("Reports to"), icon: "lucide-corner-left-up", value: card.manager?.name },
		{ label: __("Office"), icon: "lucide-map-pin", value: card.branch },
		{
			label: __("Joined"),
			icon: "lucide-calendar-check",
			value: format_date(employment.date_of_joining),
		},
		{ label: __("Type"), icon: "lucide-badge-check", value: employment.employment_type },
		{ label: __("Grade"), icon: "lucide-layers", value: employment.grade },
		{ label: __("Shift"), icon: "lucide-clock", value: employment.default_shift },
		{
			label: __("Holiday list"),
			icon: "lucide-calendar-days",
			value: employment.holiday_list,
		},
		{
			label: __("Notice period"),
			icon: "lucide-hourglass",
			value: employment.notice_number_of_days
				? __("{0} days", [employment.notice_number_of_days])
				: null,
		},
	];
});

const cover = computed(
	() => profile.value?.sections.find((section) => section.type === "Cover")?.content,
);

// Saving replaces the person's sections. They show at once, so a moved section does not jump
// back while the server saves. Saves go one at a time and a newer one replaces any still
// waiting, so quick clicks on Move up land in order. A failed save shows its message and puts
// back what the server last kept.
let saves = Promise.resolve();
let last_save = 0;

function save_sections(sections) {
	const this_save = ++last_save;
	const shown = profile.value;
	shown.saved_sections ??= shown.sections;
	shown.sections = sections;
	saves = saves.then(async () => {
		if (this_save !== last_save) return;
		try {
			shown.saved_sections = await frappe.xcall(`${API}.save_sections`, { sections });
		} catch {
			// the server's message is already on screen
		}
		if (this_save === last_save) shown.sections = shown.saved_sections;
	});
}

function set_cover(file) {
	const rest = profile.value.sections.filter((section) => section.type !== "Cover");
	save_sections([{ type: "Cover", title: "", content: file.file_url }, ...rest]);
}

function remove_cover() {
	save_sections(profile.value.sections.filter((section) => section.type !== "Cover"));
}

// the fields of each private card an employee may edit
const PERSONAL_EDITS = computed(() => {
	const options = profile.value?.options || {};
	return {
		personal: [
			{
				fieldname: "date_of_birth",
				label: __("Date of birth"),
				icon: "lucide-cake",
				type: "date",
			},
			{
				fieldname: "gender",
				label: __("Gender"),
				icon: "lucide-user-round",
				type: "select",
				options: options.gender || [],
			},
			{
				fieldname: "blood_group",
				label: __("Blood group"),
				icon: "lucide-droplet",
				type: "select",
				options: options.blood_group || [],
			},
			{
				fieldname: "marital_status",
				label: __("Marital status"),
				icon: "lucide-heart",
				type: "select",
				options: options.marital_status || [],
			},
		],
		contact: [
			{ fieldname: "cell_number", label: __("Mobile"), icon: "lucide-phone", type: "tel" },
			{
				fieldname: "personal_email",
				label: __("Personal email"),
				icon: "lucide-mail",
				type: "email",
			},
			{
				fieldname: "current_address",
				label: __("Current address"),
				icon: "lucide-house",
				type: "text",
			},
			{
				fieldname: "permanent_address",
				label: __("Permanent address"),
				icon: "lucide-map-pinned",
				type: "text",
			},
		],
		emergency: [
			{
				fieldname: "person_to_be_contacted",
				label: __("Name"),
				icon: "lucide-user-round",
				type: "data",
			},
			{ fieldname: "relation", label: __("Relation"), icon: "lucide-users", type: "data" },
			{
				fieldname: "emergency_phone_number",
				label: __("Phone"),
				icon: "lucide-phone",
				type: "tel",
			},
		],
	};
});
// what HR changes on the Employment tab
const EMPLOYMENT_EDITS = computed(() => {
	const options = profile.value?.options || {};
	const link = (fieldname, label, icon) => ({
		fieldname,
		label,
		icon,
		type: "link",
		options: options[fieldname] || [],
	});
	return [
		link("department", __("Department"), "lucide-building-2"),
		link("branch", __("Office"), "lucide-map-pin"),
		{
			fieldname: "date_of_joining",
			label: __("Joined"),
			icon: "lucide-calendar-check",
			type: "date",
			reqd: true,
			max: null,
		},
		link("employment_type", __("Type"), "lucide-badge-check"),
		link("grade", __("Grade"), "lucide-layers"),
		link("default_shift", __("Shift"), "lucide-clock"),
		link("holiday_list", __("Holiday list"), "lucide-calendar-days"),
		{
			fieldname: "notice_number_of_days",
			label: __("Notice period"),
			icon: "lucide-hourglass",
			type: "int",
			placeholder: __("Days"),
		},
	];
});
const employment_values = computed(() => {
	const data = profile.value?.private;
	if (!data) return {};
	return data.employment;
});

// HR saves someone else's details as themselves; the employee saves their own
const target = computed(() =>
	profile.value?.can_manage && !profile.value.is_self ? profile.value.card.id : null,
);

// a save gives back the private part, or that and the card, which shows the team and office
function apply(data) {
	if (data.private) {
		profile.value.private = data.private;
		profile.value.card = data.card;
	} else {
		profile.value.private = data;
	}
}

// Employment changes the card too, so it waits for the server
const editing_employment = ref(false);
const saving_employment = ref(false);

async function save_employment(values) {
	saving_employment.value = true;
	try {
		apply(
			await frappe.xcall(`${API}.save_details`, { values, employee: profile.value.card.id }),
		);
		editing_employment.value = false;
	} catch {
		// the server's message is already on screen
	} finally {
		saving_employment.value = false;
	}
}

// the card being edited, one at a time, and what was typed if its save was refused
const personal_edit = ref({ card: null, values: null });

function edit_personal(card, values = null) {
	personal_edit.value = { card, values };
}

// The card shows the new values at once and the server saves them after: ERPNext copies an
// employee's details to their user on every save, which takes about a second. The editor has
// checked the values already. If the server refuses them, desk shows why, the card shows what
// the server has, and it opens again with what was typed. Saves go one at a time, as with the
// sections, so two cards saved close together land in order.
let personal_saves = Promise.resolve();
let last_personal_save = 0;

function save_personal(values) {
	const this_save = ++last_personal_save;
	const card = personal_edit.value.card;
	const shown = profile.value;
	const saved = shown.private;
	const updated = JSON.parse(JSON.stringify(saved));
	for (const group of ["personal", "contact", "emergency"]) {
		for (const field of Object.keys(updated[group])) {
			if (field in values) updated[group][field] = values[field] || null;
		}
	}
	shown.private = updated;
	personal_edit.value = { card: null, values: null };
	personal_saves = personal_saves.then(async () => {
		try {
			const data = await frappe.xcall(`${API}.save_details`, {
				values,
				employee: target.value,
			});
			if (this_save === last_personal_save) {
				shown.private = data.private;
				shown.card = data.card;
			}
		} catch {
			// the server's message is already on screen
			if (this_save === last_personal_save) shown.private = saved;
			if (!personal_edit.value.card) edit_personal(card, values);
		}
	});
}

const personal_values = computed(() => {
	const data = profile.value?.private;
	return data ? { ...data.personal, ...data.contact, ...data.emergency } : {};
});

function open_profile(id) {
	frappe.set_route("employee-profile", id);
}
</script>

<template>
	<!-- isolate: the card's z-index stays under desk's sticky header and tabs in the form.
	The page scrolls itself; in the form, the form scrolls, so the card sticks to that. -->
	<div class="isolate" :class="!in_form && 'h-full overflow-y-auto'">
		<div v-if="error" class="flex h-full items-center justify-center p-8">
			<p class="text-base text-ink-gray-6">{{ error }}</p>
		</div>

		<div v-else-if="!profile" class="flex h-full items-center justify-center p-16">
			<LoadingIndicator class="size-5 text-ink-gray-5" />
		</div>

		<div v-else class="px-4 sm:px-6" :class="in_form ? 'pt-2' : 'pt-8'">
			<div class="mx-auto w-full max-w-6xl">
				<div
					class="group relative h-28 overflow-hidden rounded-6 bg-surface-gray-2 sm:h-44"
				>
					<img v-if="cover" :src="cover" alt="" class="size-full object-cover" />
					<div
						v-if="profile.can_edit"
						class="absolute right-3 top-3 flex gap-2 md:opacity-0 md:focus-within:opacity-100 md:group-hover:opacity-100"
					>
						<Button
							v-if="cover"
							icon="lucide-trash-2"
							:aria-label="__('Remove cover')"
							@click="remove_cover"
						/>
						<FileUploader
							:file-types="['image/*']"
							:private="false"
							optimize
							@success="set_cover"
						>
							<template #default="{ openFileSelector, uploading, progress }">
								<Button
									icon-left="lucide-image"
									:loading="uploading"
									:label="
										uploading
											? __('Uploading {0}%', [progress])
											: __('Change cover')
									"
									@click="openFileSelector"
								/>
							</template>
						</FileUploader>
					</div>
				</div>

				<div class="flex flex-col gap-8 px-4 sm:px-6 md:flex-row md:items-start md:gap-10">
					<aside
						class="relative z-10 -mt-10 sm:-mt-12 md:sticky md:mb-6 md:w-72 md:shrink-0"
						:class="
							in_form
								? 'md:top-[calc(var(--page-head-height,48px)+4.25rem)]'
								: 'md:top-6'
						"
					>
						<ProfileCard
							:card="profile.card"
							:mobile="profile.private?.contact.cell_number"
							@open_profile="open_profile"
							@open_chart="frappe.set_route('organizational-chart')"
						>
							<template #leave>
								<Badge theme="blue" :label="leave_label(profile.card.leave)">
									<template #prefix>
										<span class="lucide-tree-palm size-3" aria-hidden="true" />
									</template>
								</Badge>
							</template>
						</ProfileCard>

						<nav
							v-if="profile.private"
							class="mt-4 md:mt-6"
							:aria-label="__('Profile sections')"
						>
							<Select
								v-model="active"
								class="w-full md:hidden"
								size="md"
								:options="SECTION_OPTIONS"
							/>
							<div class="hidden flex-col gap-1 md:flex">
								<p
									class="mb-1 flex items-center gap-2 px-4 text-sm text-ink-gray-5"
								>
									<span class="lucide-users size-4 shrink-0" />
									{{ __("Everyone at {0}", [profile.card.company]) }}
								</p>
								<Button
									class="w-full !justify-start !px-4 !font-normal"
									:variant="active === 'public' ? 'subtle' : 'ghost'"
									:label="__('Public profile')"
									@click="active = 'public'"
								>
									<template #prefix>
										<span class="lucide-user-round size-4" />
									</template>
								</Button>
								<p
									class="mb-1 mt-4 flex items-center gap-2 px-4 text-sm text-ink-gray-5"
								>
									<span class="lucide-lock size-4 shrink-0" />
									{{
										profile.is_self
											? __("Only you and HR")
											: __("Only {0} and HR", [profile.card.name])
									}}
								</p>
								<Button
									v-for="section in SECTIONS"
									:key="section.value"
									class="w-full !justify-start !px-4 !font-normal"
									:variant="active === section.value ? 'subtle' : 'ghost'"
									:label="section.label"
									@click="active = section.value"
								>
									<template #prefix>
										<span :class="section.icon" class="size-4" />
									</template>
									<template v-if="section.count" #suffix>
										<Badge
											theme="gray"
											:label="String(section.count)"
											class="ml-auto"
										/>
									</template>
								</Button>
							</div>
						</nav>
					</aside>

					<!-- With the bottom space inside, and tall enough that a short tab, Bank or Assets, scrolls
					until the card reaches where it pins and no further, so the cover stays behind the card.
					That is the screen, less the card's pinned top and its 3rem overlap with the cover. -->
					<div
						class="min-w-0 flex-1 pb-24 md:pt-8"
						:class="
							in_form
								? 'md:min-h-[calc(100vh-var(--page-head-height,48px)-7.25rem)]'
								: 'md:min-h-[calc(100vh-var(--page-head-height,48px)-4.5rem)]'
						"
					>
						<!-- the side's group labels, for a phone, where a picker stands in for the side -->
						<p
							v-if="profile.private"
							class="mb-6 flex items-center gap-2 text-sm text-ink-gray-5 md:hidden"
						>
							<span
								:class="active === 'public' ? 'lucide-users' : 'lucide-lock'"
								class="size-4 shrink-0"
							/>
							{{
								active === "public"
									? __("Everyone at {0} sees this", [profile.card.company])
									: profile.is_self
									  ? __("Only you and HR see this")
									  : __("Only {0} and HR see this", [profile.card.name])
							}}
						</p>

						<PublicProfile
							v-if="active === 'public'"
							:sections="profile.sections"
							:name="profile.card.name"
							:can_edit="profile.can_edit"
							@save="save_sections"
						/>

						<div v-else-if="active === 'personal'" class="space-y-12">
							<DetailCard
								v-for="card in [
									{
										name: 'personal',
										title: __('Personal details'),
										rows: personal_rows,
									},
									{ name: 'contact', title: __('Contact'), rows: contact_rows },
								]"
								:key="card.name"
								:title="card.title"
								:rows="card.rows"
							>
								<template
									v-if="
										profile.can_edit_details &&
										personal_edit.card !== card.name
									"
									#actions
								>
									<Button
										variant="ghost"
										icon-left="lucide-pencil"
										:label="__('Edit')"
										@click="edit_personal(card.name)"
									/>
								</template>
								<template v-if="personal_edit.card === card.name" #default>
									<CardEditor
										:fields="PERSONAL_EDITS[card.name]"
										:values="personal_edit.values || personal_values"
										@save="save_personal"
										@cancel="personal_edit.card = null"
									/>
								</template>
							</DetailCard>
							<DetailCard
								v-if="personal_edit.card === 'emergency'"
								:title="__('Emergency contact')"
							>
								<CardEditor
									:fields="PERSONAL_EDITS.emergency"
									:values="personal_edit.values || personal_values"
									@save="save_personal"
									@cancel="personal_edit.card = null"
								/>
							</DetailCard>
							<section v-else>
								<div class="mb-2 flex min-h-8 items-center gap-2">
									<h2 class="text-base-semibold text-ink-gray-9">
										{{ __("Emergency contact") }}
									</h2>
									<div
										v-if="profile.can_edit_details"
										class="ml-auto flex items-center gap-1"
									>
										<Button
											variant="ghost"
											:icon-left="
												emergency.person_to_be_contacted
													? 'lucide-pencil'
													: 'lucide-plus'
											"
											:label="
												emergency.person_to_be_contacted
													? __('Edit')
													: __('Add')
											"
											@click="edit_personal('emergency')"
										/>
									</div>
								</div>
								<div
									v-if="emergency.person_to_be_contacted"
									class="flex items-center gap-3 rounded-6 border border-outline-gray-1 px-4 py-3"
								>
									<div class="min-w-0 flex-1">
										<div class="truncate text-base text-ink-gray-8">
											{{ emergency.person_to_be_contacted }}
										</div>
										<div
											v-if="emergency.relation"
											class="mt-0.5 truncate text-sm text-ink-gray-5"
										>
											{{ emergency.relation }}
										</div>
									</div>
									<span class="shrink-0 text-base tabular-nums text-ink-gray-7">
										{{ emergency.emergency_phone_number }}
									</span>
								</div>
								<p v-else class="text-base text-ink-gray-6">
									{{ __("No emergency contact yet") }}
								</p>
							</section>
						</div>

						<BankSection
							v-else-if="active === 'bank'"
							:employee="profile.card.id"
							:bank="profile.private.bank"
							:request="profile.private.bank_request"
							:can_edit="profile.is_self"
							:can_manage="Boolean(target)"
							:can_review="profile.can_review['Bank Details Change Request']"
							:has_ifsc="'ifsc_code' in profile.private.bank"
							@saved="apply"
						/>

						<DocumentsSection
							v-else-if="active === 'documents'"
							:employee="profile.card.id"
							:documents="profile.private.documents"
							:document_types="profile.options?.document_types || []"
							:can_edit="profile.is_self"
							:can_manage="Boolean(target)"
							@saved="apply"
						/>

						<AssetsSection
							v-else-if="active === 'assets'"
							:assets="profile.private.assets"
							:requests="profile.private.asset_requests"
							:asset_categories="profile.options?.asset_categories || []"
							:can_edit="profile.is_self"
							:can_review="profile.can_review['Asset Request']"
							@saved="apply"
						/>

						<div v-else-if="active === 'employment'" class="space-y-6">
							<DetailCard :title="__('Job details')" :rows="employment_rows">
								<template
									v-if="profile.can_manage && !editing_employment"
									#actions
								>
									<Button
										variant="ghost"
										icon-left="lucide-pencil"
										:label="__('Edit')"
										@click="editing_employment = true"
									/>
								</template>
								<template v-if="editing_employment" #default>
									<CardEditor
										:fields="EMPLOYMENT_EDITS"
										:values="employment_values"
										:saving="saving_employment"
										@save="save_employment"
										@cancel="editing_employment = false"
									/>
								</template>
							</DetailCard>
							<p v-if="!profile.can_manage" class="text-sm text-ink-gray-5">
								{{
									__(
										"Kept by HR. To change something here, talk to your manager or HR.",
									)
								}}
							</p>
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>
