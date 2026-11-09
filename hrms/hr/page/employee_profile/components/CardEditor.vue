<script setup>
import { computed, ref } from "vue";
import {
	Button,
	Checkbox,
	DatePicker,
	FileUploader,
	Select,
	TextInput,
	Textarea,
} from "frappe-ui";

// Edits one private card where it is shown, in the card's own label and value rows
const props = defineProps({
	// [{ fieldname, label, icon, type, reqd?, options?, min?, max?, placeholder? }], type one of
	// data, tel, email, int, text, select, link, date or file. A link searches its options, given
	// as values or as { label, value }; a file is uploaded private and its URL is the value.
	fields: { type: Array, default: () => [] },
	values: { type: Object, default: () => ({}) },
	save_label: { type: String, default: null },
	// while the server checks a request it must accept first
	saving: { type: Boolean, default: false },
});
const emit = defineEmits(["save", "cancel"]);

const __ = window.__;
const frappe = window.frappe;

const draft = ref(
	Object.fromEntries(
		props.fields.map((field) => [
			field.fieldname,
			String(props.values[field.fieldname] ?? ""),
		]),
	),
);
const errors = ref({});
const file_names = ref({});

// the site's date format, as dayjs writes it: dd-mm-yyyy is DD-MM-YYYY
const date_format = (frappe.boot.sysdefaults.date_format || "dd-mm-yyyy").toUpperCase();
const today = frappe.datetime.get_today();

// frappe-ui's DatePicker reads a typed "17101999" year first, as 1711. Until it tries the
// format without separators itself, 8 typed digits are spelled out in the site's format,
// "17-10-1999", as they are typed: the picker reads the text on Enter, on blur, and also when a
// click outside closes it, which comes before the blur.
function spell_out_date(event) {
	const input = event.target;
	if (input.tagName !== "INPUT" || !/^\d{8}$/.test(input.value)) return;
	const digits = input.value;
	const separator = date_format.match(/[^A-Z]/)?.[0] || "-";
	let at = 0;
	input.value = date_format
		.split(/[^A-Z]+/)
		.map((token) => digits.slice(at, (at += token.length)))
		.join(separator);
}

const has_addresses = computed(() =>
	["current_address", "permanent_address"].every((name) =>
		props.fields.some((field) => field.fieldname === name),
	),
);
const same_address = ref(
	has_addresses.value &&
		Boolean(draft.value.current_address) &&
		draft.value.current_address === draft.value.permanent_address,
);

// the server checks these too; here they show at once, under the field
function check(field, value) {
	if (!value) return field.reqd ? __("Required") : null;
	if (field.type === "email" && !frappe.utils.validate_type(value, "email")) {
		return __("Enter a valid email address");
	}
	if (field.type === "int" && !/^\d+$/.test(value)) return __("Enter a whole number");
	if (field.type === "tel") {
		const digits = value.replace(/\D/g, "").length;
		if (!/^\+?[\d\s()-]+$/.test(value) || digits < 7 || digits > 15) {
			return __("Enter a phone number of 7 to 15 digits");
		}
	}
	return null;
}

function save() {
	const values = {};
	errors.value = {};
	for (const field of props.fields) {
		values[field.fieldname] = draft.value[field.fieldname].trim();
		const error = check(field, values[field.fieldname]);
		if (error) errors.value[field.fieldname] = error;
	}
	if (Object.keys(errors.value).length) return;
	if (same_address.value) values.permanent_address = values.current_address;
	emit("save", values);
}

// a link's options as { label, value }, and a "None" to clear it when it is not required
function link_options(field) {
	const options = field.options.map((option) =>
		typeof option === "string" ? { label: option, value: option } : option,
	);
	return field.reqd ? options : [{ label: __("None"), value: "" }, ...options];
}
</script>

<template>
	<form class="py-2" @submit.prevent="save">
		<div class="space-y-3">
			<!-- on a phone the label goes above its input, which then has the card's width -->
			<div
				v-for="field in fields"
				:key="field.fieldname"
				class="flex flex-col gap-1.5 sm:flex-row sm:items-start sm:gap-3"
			>
				<label
					:for="`profile-${field.fieldname}`"
					class="flex h-7 shrink-0 items-center gap-2 text-base text-ink-gray-5 sm:w-40"
				>
					<span :class="field.icon" class="size-4 shrink-0" aria-hidden="true" />
					<span class="truncate">{{ field.label }}</span>
				</label>

				<div class="min-w-0 flex-1">
					<div v-if="field.type === 'date'" @input.capture="spell_out_date">
						<DatePicker
							:id="`profile-${field.fieldname}`"
							v-model="draft[field.fieldname]"
							class="w-full"
							:format="date_format"
							:min="field.min || '1900-01-01'"
							:max="field.max === undefined ? today : field.max"
							:error="errors[field.fieldname]"
							typeable
						/>
					</div>

					<div v-else-if="field.type === 'file'" class="flex flex-col gap-1">
						<FileUploader
							:file-types="['image/*', 'application/pdf']"
							:private="true"
							@success="
								(file) => {
									draft[field.fieldname] = file.file_url;
									file_names[field.fieldname] = file.file_name;
								}
							"
						>
							<template #default="{ openFileSelector, uploading, progress }">
								<div class="flex min-h-7 items-center gap-2">
									<Button
										:icon-left="
											draft[field.fieldname]
												? 'lucide-refresh-cw'
												: 'lucide-upload'
										"
										:loading="uploading"
										:label="
											uploading
												? __('Uploading {0}%', [progress])
												: draft[field.fieldname]
												  ? __('Replace')
												  : __('Upload')
										"
										@click="openFileSelector"
									/>
									<span
										v-if="file_names[field.fieldname]"
										class="min-w-0 truncate text-base text-ink-gray-7"
									>
										{{ file_names[field.fieldname] }}
									</span>
								</div>
							</template>
						</FileUploader>
						<p v-if="field.description" class="text-sm text-ink-gray-5">
							{{ field.description }}
						</p>
						<p v-if="errors[field.fieldname]" class="text-sm text-ink-red-4">
							{{ errors[field.fieldname] }}
						</p>
					</div>

					<Select
						v-else-if="field.type === 'select'"
						:id="`profile-${field.fieldname}`"
						v-model="draft[field.fieldname]"
						class="w-full"
						:options="field.options.map((value) => ({ label: value, value }))"
						:placeholder="__('Select')"
						:error="errors[field.fieldname]"
					/>

					<Select
						v-else-if="field.type === 'link'"
						:id="`profile-${field.fieldname}`"
						:model-value="draft[field.fieldname] || (field.reqd ? null : '')"
						class="w-full"
						:options="link_options(field)"
						:placeholder="field.placeholder || __('Select')"
						:error="errors[field.fieldname]"
						@update:model-value="(value) => (draft[field.fieldname] = value || '')"
					/>

					<div
						v-else-if="
							field.type === 'text' && field.fieldname === 'permanent_address'
						"
						class="flex flex-col gap-2"
					>
						<Checkbox
							v-if="has_addresses"
							v-model="same_address"
							class="h-7"
							:label="__('Same as current address')"
						/>
						<Textarea
							v-if="!same_address"
							:id="`profile-${field.fieldname}`"
							v-model="draft[field.fieldname]"
							:rows="2"
						/>
					</div>

					<Textarea
						v-else-if="field.type === 'text'"
						:id="`profile-${field.fieldname}`"
						v-model="draft[field.fieldname]"
						:rows="2"
						:error="errors[field.fieldname]"
					/>

					<TextInput
						v-else
						:id="`profile-${field.fieldname}`"
						v-model="draft[field.fieldname]"
						:type="{ data: 'text', int: 'number' }[field.type] || field.type"
						:placeholder="field.placeholder"
						:error="errors[field.fieldname]"
					/>
				</div>
			</div>
		</div>

		<div class="mt-4 flex justify-end gap-2">
			<Button :label="__('Cancel')" :disabled="saving" @click="emit('cancel')" />
			<Button
				variant="solid"
				:label="save_label || __('Save')"
				:loading="saving"
				@click="save"
			/>
		</div>
	</form>
</template>
