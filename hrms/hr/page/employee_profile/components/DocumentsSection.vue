<script setup>
import { computed, nextTick, ref } from "vue";
import { Badge, Button, Dialog, Dropdown, FileUploader, Textarea } from "frappe-ui";
import CardEditor from "./CardEditor.vue";
import ListRow, { LIST_CLASS } from "./ListRow.vue";
import PropertyRow from "./PropertyRow.vue";
import { API, short_date } from "../utils.js";

// The documents HR keeps for the employee. Each one is a file on the Employee, and counts once HR
// has checked it. The employee uploads their own; HR checks them, asks for one by a date, or
// uploads one for the employee, which counts at once.
const props = defineProps({
	employee: { type: String, required: true },
	documents: { type: Array, default: () => [] },
	// [{ name, has_number, has_expiry }]
	document_types: { type: Array, default: () => [] },
	// the employee's own
	can_edit: { type: Boolean, default: false },
	// HR's, on someone else's
	can_manage: { type: Boolean, default: false },
});
const emit = defineEmits(["saved"]);

const __ = window.__;
const frappe = window.frappe;

const STATUS = {
	Missing: { theme: "gray", label: __("Required") },
	Pending: { theme: "amber", label: __("Pending") },
	Submitted: { theme: "blue", label: __("In review") },
	Verified: { theme: "green", label: __("On file") },
	Rejected: { theme: "red", label: __("Rejected") },
};
// what still needs the employee: asked for, not given yet, or sent back
const DUE = ["Missing", "Pending", "Rejected"];
const due = computed(() => props.documents.filter((doc) => DUE.includes(doc.status)).length);

// one line of facts under the name, as the badge already says where the document stands; HR's
// reason for sending it back gets a line of its own
function details(doc) {
	const facts = [
		doc.document_number,
		doc.expiry_date && __("Expires {0}", [short_date(doc.expiry_date)]),
	].filter(Boolean);
	const lines = [];
	if (doc.due_date && DUE.includes(doc.status)) {
		lines.push({ text: __("Due {0}", [short_date(doc.due_date)]), tone: "text-ink-amber-7" });
	}
	// not on a phone, where the row has no room for it; the record has it
	if (facts.length) lines.push({ text: facts.join(" · "), wide_only: true });
	if (doc.remarks) lines.push({ text: doc.remarks, tone: "text-ink-red-7" });
	return lines;
}

// the employee takes back their own upload until HR has verified the document once; HR removes any
const can_remove = (doc) =>
	props.can_manage
		? doc.status !== "Missing"
		: props.can_edit &&
		  doc.attachment &&
		  !doc.verified_on &&
		  ["Submitted", "Rejected"].includes(doc.status);
const removing = ref({ open: false, doc: null, saving: false });

const type_of = (name) => props.document_types.find((type) => type.name === name) || {};
const not_listed = computed(() =>
	props.document_types.filter(
		(type) => !props.documents.some((doc) => doc.document_type === type.name),
	),
);
const add_options = computed(() =>
	not_listed.value.map((type) => ({
		label: type.name,
		onClick: () =>
			props.can_manage
				? (asking.value = { open: true, document_type: type.name, saving: false })
				: start_upload({ document_type: type.name, ...type }),
	})),
);

// HR's other actions on a row: upload the document for the employee, or ask for it again
function row_options(doc) {
	return [
		{
			label: doc.attachment ? __("Replace for them") : __("Upload for them"),
			icon: "lucide-upload",
			onClick: () => start_upload(doc),
		},
		{
			label: __("Ask for it again"),
			icon: "lucide-bell",
			onClick: () =>
				(asking.value = { open: true, document_type: doc.document_type, saving: false }),
		},
		can_remove(doc) && {
			label: __("Remove"),
			icon: "lucide-trash-2",
			theme: "red",
			onClick: () => (removing.value = { open: true, doc, saving: false }),
		},
	].filter(Boolean);
}

// An upload opens a dialog when the document has a number or an expiry date, and always for HR,
// so they see whose record it goes on; the rest upload at once
const dialog = ref({ open: false, doc: null, saving: false });
const dialog_fields = computed(() => {
	const doc = dialog.value.doc;
	if (!doc) return [];
	return [
		{
			fieldname: "file_url",
			label: __("File"),
			icon: "lucide-paperclip",
			type: "file",
			reqd: true,
		},
		doc.has_number && {
			fieldname: "document_number",
			label: __("Number"),
			icon: "lucide-hash",
			type: "data",
			reqd: true,
		},
		doc.has_expiry && {
			fieldname: "expiry_date",
			label: __("Expires on"),
			icon: "lucide-calendar",
			type: "date",
			min: frappe.datetime.get_today(),
			max: null,
		},
	].filter(Boolean);
});

function start_upload(doc) {
	dialog.value = { open: true, doc: { ...type_of(doc.document_type), ...doc }, saving: false };
}

async function call(method, args, state) {
	if (state) state.saving = true;
	try {
		emit("saved", await frappe.xcall(`${API}.${method}`, args));
		if (state) state.open = false;
		return true;
	} catch {
		// the server's message is already on screen
	} finally {
		if (state) state.saving = false;
	}
}

const upload = (document_type, values) =>
	call(
		"upload_document",
		{ document_type, ...values, employee: props.can_manage ? props.employee : null },
		dialog.value,
	);

// HR asks for a document, by a date if they give one
const asking = ref({ open: false, document_type: null, saving: false });
const ASK_FIELDS = [
	{
		fieldname: "due_date",
		label: __("Needed by"),
		icon: "lucide-calendar",
		type: "date",
		min: frappe.datetime.get_today(),
		max: null,
	},
];

// HR checks an upload: on file, or back to the employee with what is wrong
// Reject first asks what is wrong, so a note is never typed for a verified document and lost
const reviewing = ref({
	open: false,
	doc: null,
	rejecting: false,
	remarks: "",
	error: null,
	saving: false,
});

const remarks_input = ref(null);

async function ask_remarks() {
	reviewing.value.rejecting = true;
	await nextTick();
	remarks_input.value?.focus();
}

function review(status) {
	const state = reviewing.value;
	if (status === "Rejected" && !state.remarks.trim()) {
		state.error = __("Say what is wrong, so they can fix it");
		return;
	}
	call(
		"review_document",
		{
			employee: props.employee,
			document_type: state.doc.document_type,
			status,
			remarks: status === "Rejected" ? state.remarks : null,
		},
		state,
	);
}
</script>

<template>
	<section>
		<div class="mb-2 flex min-h-8 items-center gap-2">
			<h2 class="text-base-semibold text-ink-gray-9">{{ __("Documents") }}</h2>
			<Badge v-if="due" theme="gray" :label="__('{0} due', [due])" />
			<div v-if="(can_edit || can_manage) && add_options.length" class="ml-auto">
				<Dropdown :options="add_options">
					<Button
						variant="ghost"
						icon-left="lucide-plus"
						:label="can_manage ? __('Ask for a document') : __('Add a document')"
					/>
				</Dropdown>
			</div>
		</div>

		<div v-if="documents.length" :class="LIST_CLASS">
			<ListRow v-for="doc in documents" :key="doc.document_type" icon="lucide-file-text">
				<a
					v-if="doc.attachment"
					:href="doc.attachment"
					target="_blank"
					rel="noopener noreferrer"
					class="hover:underline"
				>
					{{ doc.document_type }}
				</a>
				<template v-else>{{ doc.document_type }}</template>

				<template #details>
					<div
						v-for="line in details(doc)"
						:key="line.text"
						class="mt-0.5 break-words text-sm"
						:class="[
							line.tone || 'text-ink-gray-5',
							line.wide_only && 'hidden sm:block',
						]"
					>
						{{ line.text }}
					</div>
				</template>

				<template v-if="STATUS[doc.status]" #badge>
					<Badge v-bind="STATUS[doc.status]" />
				</template>

				<template v-if="can_manage" #actions>
					<Button
						v-if="doc.status === 'Submitted'"
						:label="__('Review')"
						@click="
							reviewing = {
								open: true,
								doc,
								rejecting: false,
								remarks: '',
								error: null,
								saving: false,
							}
						"
					/>
					<Dropdown :options="row_options(doc)">
						<Button
							variant="ghost"
							icon="lucide-ellipsis"
							:aria-label="__('More for {0}', [doc.document_type])"
						/>
					</Dropdown>
				</template>
				<template v-else-if="can_edit" #actions>
					<Button
						v-if="doc.has_number || doc.has_expiry"
						variant="ghost"
						:icon-left="doc.attachment ? 'lucide-refresh-cw' : 'lucide-upload'"
						:label="doc.attachment ? __('Replace') : __('Upload')"
						@click="start_upload(doc)"
					/>
					<FileUploader
						v-else
						:file-types="['image/*', 'application/pdf']"
						:private="true"
						@success="(file) => upload(doc.document_type, { file_url: file.file_url })"
					>
						<template #default="{ openFileSelector, uploading, progress }">
							<Button
								variant="ghost"
								:icon-left="doc.attachment ? 'lucide-refresh-cw' : 'lucide-upload'"
								:loading="uploading"
								:label="
									uploading
										? __('Uploading {0}%', [progress])
										: doc.attachment
										  ? __('Replace')
										  : __('Upload')
								"
								@click="openFileSelector"
							/>
						</template>
					</FileUploader>
					<Button
						v-if="can_remove(doc)"
						variant="ghost"
						icon="lucide-trash-2"
						:aria-label="__('Remove {0}', [doc.document_type])"
						:tooltip="__('Remove')"
						@click="removing = { open: true, doc, saving: false }"
					/>
				</template>
			</ListRow>
		</div>
		<p v-else class="text-base text-ink-gray-6">{{ __("No documents yet") }}</p>

		<p class="mt-3 text-sm text-ink-gray-5">
			{{
				can_manage
					? __("PDF or image. A document you upload for them counts as on file at once.")
					: __("PDF or image. HR checks each upload before it counts as on file.")
			}}
		</p>

		<!-- not closed by a click outside: inside the page's shadow root, reka-ui takes a click on
		the date picker's calendar for one -->
		<Dialog
			v-if="can_edit || can_manage"
			v-model="dialog.open"
			:dismissible="false"
			:title="dialog.doc ? __('Upload {0}', [dialog.doc.document_type]) : ''"
		>
			<CardEditor
				v-if="dialog.open"
				:fields="dialog_fields"
				:values="dialog.doc"
				:save_label="__('Upload')"
				:saving="dialog.saving"
				@save="(values) => upload(dialog.doc.document_type, values)"
				@cancel="dialog.open = false"
			/>
		</Dialog>

		<Dialog
			v-if="can_edit || can_manage"
			v-model="removing.open"
			:title="removing.doc ? __('Remove {0}?', [removing.doc.document_type]) : ''"
		>
			<p v-if="removing.doc" class="text-p-base text-ink-gray-7">
				{{
					can_manage
						? __("It comes off their record, with the file they gave.")
						: __("Your upload is taken back before HR checks it.")
				}}
			</p>
			<template #actions>
				<div v-if="removing.doc" class="flex justify-end gap-2">
					<Button :label="__('Keep')" @click="removing.open = false" />
					<Button
						variant="solid"
						theme="red"
						:label="__('Remove')"
						:loading="removing.saving"
						@click="
							call(
								'remove_document',
								{
									document_type: removing.doc.document_type,
									employee: can_manage ? employee : null,
								},
								removing,
							)
						"
					/>
				</div>
			</template>
		</Dialog>

		<template v-if="can_manage">
			<Dialog
				v-model="asking.open"
				:dismissible="false"
				:title="asking.document_type ? __('Ask for {0}', [asking.document_type]) : ''"
			>
				<CardEditor
					v-if="asking.open"
					:fields="ASK_FIELDS"
					:save_label="__('Ask')"
					:saving="asking.saving"
					@save="
						(values) =>
							call(
								'request_document',
								{ employee, document_type: asking.document_type, ...values },
								asking,
							)
					"
					@cancel="asking.open = false"
				/>
			</Dialog>

			<Dialog
				v-model="reviewing.open"
				:title="reviewing.doc ? __('Review {0}', [reviewing.doc.document_type]) : ''"
			>
				<div v-if="reviewing.doc">
					<PropertyRow
						:label="__('File')"
						icon="lucide-paperclip"
						:value="__('Open')"
						:href="reviewing.doc.attachment"
					/>
					<PropertyRow
						v-if="reviewing.doc.has_number"
						:label="__('Number')"
						icon="lucide-hash"
						:value="reviewing.doc.document_number"
					/>
					<PropertyRow
						v-if="reviewing.doc.has_expiry"
						:label="__('Expires on')"
						icon="lucide-calendar"
						:value="short_date(reviewing.doc.expiry_date)"
					/>
					<div v-if="reviewing.rejecting" class="mt-3">
						<Textarea
							ref="remarks_input"
							v-model="reviewing.remarks"
							:label="__('What is wrong with it?')"
							:rows="3"
							:placeholder="__('The employee sees this')"
							:error="reviewing.error"
						/>
					</div>
				</div>
				<template #actions>
					<div v-if="reviewing.rejecting" class="flex justify-end gap-2">
						<Button :label="__('Back')" @click="reviewing.rejecting = false" />
						<Button
							variant="solid"
							theme="red"
							:label="__('Reject')"
							:loading="reviewing.saving"
							@click="review('Rejected')"
						/>
					</div>
					<div v-else class="flex justify-end gap-2">
						<Button
							:label="__('Reject')"
							:disabled="reviewing.saving"
							@click="ask_remarks"
						/>
						<Button
							variant="solid"
							icon-left="lucide-check"
							:label="__('Verify')"
							:loading="reviewing.saving"
							@click="review('Verified')"
						/>
					</div>
				</template>
			</Dialog>
		</template>
	</section>
</template>
