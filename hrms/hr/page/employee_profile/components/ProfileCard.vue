<script setup>
import { computed, ref } from "vue";
import { Avatar, Badge, Button, Tooltip } from "frappe-ui";

const props = defineProps({
	card: { type: Object, required: true },
	// only the employee and HR get the mobile number
	mobile: { type: String, default: null },
});
const emit = defineEmits(["open_profile", "open_chart"]);

const __ = window.__;
const lang = window.frappe?.boot?.lang;

const show_mobile = ref(false);
// only the last four digits stay, as in +•• ••••• •4477
const masked_mobile = computed(() => {
	if (!props.mobile) return null;
	let hidden = props.mobile.replace(/\D/g, "").length - 4;
	return props.mobile.replace(/\d/g, (digit) => (hidden-- > 0 ? "•" : digit));
});

const tenure_text = computed(() => {
	const tenure = props.card.tenure;
	if (!tenure) return null;
	if (tenure.years) {
		return tenure.years === 1
			? __("1 year at {0}", [props.card.company])
			: __("{0} years at {1}", [tenure.years, props.card.company]);
	}
	if (tenure.months) {
		return tenure.months === 1
			? __("1 month at {0}", [props.card.company])
			: __("{0} months at {1}", [tenure.months, props.card.company]);
	}
	return __("Joined {0} recently", [props.card.company]);
});

const birthday_text = computed(() => {
	const birthday = props.card.birthday;
	if (!birthday) return null;
	const month = new Date(2000, birthday.month - 1, 1).toLocaleDateString(lang, {
		month: "short",
	});
	// in the order of the site's date format: 14 Mar for dd-mm-yyyy, Mar 14 for mm-dd-yyyy
	const day_first = !window.frappe?.boot?.sysdefaults?.date_format?.startsWith("mm");
	return day_first ? `${birthday.day} ${month}` : `${month} ${birthday.day}`;
});

const reports_text = computed(() =>
	props.card.reports === 1
		? __("1 direct report")
		: __("{0} direct reports", [props.card.reports]),
);

// On a phone the card shows its first three rows and folds the rest under "Show more", as in
// the sketch, so the sections below it stay in sight
const PHONE_ROWS = 3;
const rows = computed(() =>
	[
		props.card.department && "department",
		props.card.branch && "branch",
		props.card.manager && "manager",
		props.card.reports && "reports",
		tenure_text.value && "tenure",
		props.card.email && "email",
		props.mobile && "mobile",
		birthday_text.value && "birthday",
	].filter(Boolean),
);
const expanded = ref(false);
const folded = computed(() => (expanded.value ? 0 : Math.max(rows.value.length - PHONE_ROWS, 0)));
const fold = (row) => folded.value && rows.value.indexOf(row) >= PHONE_ROWS && "max-md:hidden";

function copy_email() {
	navigator.clipboard?.writeText(props.card.email);
	window.frappe?.show_alert({ message: __("Email copied"), indicator: "green" });
}
</script>

<template>
	<div class="rounded-6 border border-outline-gray-1 bg-surface-base">
		<div class="flex items-start gap-3 p-4">
			<Avatar :image="card.image" :label="card.name" size="2xl" />
			<div class="min-w-0 flex-1">
				<h1 class="break-words text-lg-semibold text-ink-gray-9">{{ card.name }}</h1>
				<p class="mt-0.5 line-clamp-2 text-base text-ink-gray-6">{{ card.designation }}</p>
			</div>
		</div>

		<div class="border-t border-outline-gray-1 px-4 py-3">
			<dl>
				<div
					v-if="card.department"
					:class="fold('department')"
					class="flex h-8 items-center gap-3"
				>
					<dt class="sr-only">{{ __("Team") }}</dt>
					<span class="lucide-building-2 size-4 shrink-0 text-ink-gray-5" />
					<dd class="min-w-0 truncate text-base text-ink-gray-8">
						{{ card.department }}
					</dd>
				</div>
				<div
					v-if="card.branch"
					:class="fold('branch')"
					class="flex h-8 items-center gap-3"
				>
					<dt class="sr-only">{{ __("Office") }}</dt>
					<span class="lucide-map-pin size-4 shrink-0 text-ink-gray-5" />
					<dd class="min-w-0 truncate text-base text-ink-gray-8">{{ card.branch }}</dd>
				</div>
				<div
					v-if="card.manager"
					:class="fold('manager')"
					class="flex h-8 items-center gap-3"
				>
					<dt class="sr-only">{{ __("Manager") }}</dt>
					<span class="flex size-4 shrink-0 items-center justify-center">
						<Avatar :image="card.manager.image" :label="card.manager.name" size="xs" />
					</span>
					<dd class="min-w-0 truncate text-base">
						<button
							type="button"
							class="text-ink-gray-8 hover:underline"
							@click="emit('open_profile', card.manager.id)"
						>
							{{ card.manager.name }}
						</button>
						<span class="ml-1.5 text-ink-gray-5">{{ __("Manager") }}</span>
					</dd>
				</div>
				<div
					v-if="card.reports"
					:class="fold('reports')"
					class="flex h-8 items-center gap-3"
				>
					<dt class="sr-only">{{ __("Manages") }}</dt>
					<span class="lucide-users size-4 shrink-0 text-ink-gray-5" />
					<dd class="min-w-0 truncate text-base">
						<button
							type="button"
							class="text-ink-gray-8 hover:underline"
							@click="emit('open_chart')"
						>
							{{ reports_text }}
						</button>
					</dd>
				</div>
				<div
					v-if="tenure_text"
					:class="fold('tenure')"
					class="flex h-8 items-center gap-3"
				>
					<dt class="sr-only">{{ __("Tenure") }}</dt>
					<span class="lucide-calendar-check size-4 shrink-0 text-ink-gray-5" />
					<dd class="min-w-0 truncate text-base text-ink-gray-8">{{ tenure_text }}</dd>
				</div>
				<div
					v-if="card.email"
					:class="fold('email')"
					class="group flex h-8 items-center gap-3"
				>
					<dt class="sr-only">{{ __("Email") }}</dt>
					<span class="lucide-mail size-4 shrink-0 text-ink-gray-5" />
					<dd class="min-w-0 flex-1 truncate text-base text-ink-gray-8">
						<a :href="`mailto:${card.email}`" class="hover:underline">{{
							card.email
						}}</a>
					</dd>
					<Tooltip :text="__('Copy email')">
						<Button
							variant="ghost"
							icon="lucide-copy"
							class="opacity-0 focus-visible:opacity-100 group-hover:opacity-100 [@media(hover:none)]:opacity-100"
							:aria-label="__('Copy email')"
							@click="copy_email"
						/>
					</Tooltip>
				</div>
				<div v-if="mobile" :class="fold('mobile')" class="flex h-8 items-center gap-3">
					<dt class="sr-only">{{ __("Mobile") }}</dt>
					<span class="lucide-phone size-4 shrink-0 text-ink-gray-5" />
					<dd class="min-w-0 flex-1 truncate text-base tabular-nums text-ink-gray-8">
						{{ show_mobile ? mobile : masked_mobile }}
					</dd>
					<Tooltip :text="show_mobile ? __('Hide') : __('Show')">
						<Button
							variant="ghost"
							:icon="show_mobile ? 'lucide-eye-off' : 'lucide-eye'"
							:aria-label="show_mobile ? __('Hide mobile') : __('Show mobile')"
							@click="show_mobile = !show_mobile"
						/>
					</Tooltip>
				</div>
				<div
					v-if="birthday_text"
					:class="fold('birthday')"
					class="flex h-8 items-center gap-3"
				>
					<dt class="sr-only">{{ __("Birthday") }}</dt>
					<span class="lucide-cake size-4 shrink-0 text-ink-gray-5" />
					<dd class="min-w-0 flex-1 truncate text-base text-ink-gray-8">
						{{ birthday_text }}
					</dd>
				</div>
			</dl>
			<button
				v-if="folded"
				type="button"
				class="flex h-8 items-center text-base text-ink-gray-8 hover:underline md:hidden"
				@click="expanded = true"
			>
				{{ __("Show {0} more", [folded]) }}
			</button>
		</div>

		<div v-if="card.leave" class="border-t border-outline-gray-1 px-4 py-3">
			<slot name="leave" />
		</div>
	</div>
</template>
