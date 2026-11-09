<script setup>
import { computed, ref } from "vue";
import { Badge, Button, Dialog, Dropdown, FileUploader, Textarea } from "frappe-ui";
import CardEditor from "./CardEditor.vue";
import ListRow from "./ListRow.vue";
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

function details(doc) {
	const lines = [];
	if (doc.due_date && DUE.includes(doc.status)) {
		lines.push({ text: __("Due {0}", [short_date(doc.due_date)]), tone: "text-ink-amber-3" });
	}
	if (doc.status === "Submitted") {
		lines.push({
			text: props.can_manage ? __("Waiting for your check") : __("With HR for checking"),
		});
	}
	if (doc.document_number) lines.push({ text: doc.document_number });
	if (doc.expiry_date) lines.push({ text: __("Expires {0}", [short_date(doc.expiry_date)]) });
	if (doc.remarks) lines.push({ text: doc.remarks });
	return lines;
}

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
	];
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
const reviewing = ref({ open: false, doc: null, remarks: "", error: null, saving: false });

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

		<div
			v-if="documents.length"
			class="flex flex-col gap-px rounded-6 border border-outline-gray-1 p-1"
		>
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
						class="mt-0.5 truncate text-sm"
						:class="line.tone || 'text-ink-gray-5'"
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

		<Dialog
			v-if="can_edit || can_manage"
			v-model="dialog.open"
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

		<template v-if="can_manage">
			<Dialog
				v-model="asking.open"
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
					<div class="mt-3">
						<Textarea
							v-model="reviewing.remarks"
							:rows="2"
							:placeholder="__('If you reject it, say what is wrong')"
							:error="reviewing.error"
						/>
					</div>
				</div>
				<template #actions>
					<div class="flex justify-end gap-2">
						<Button
							:label="__('Reject')"
							:disabled="reviewing.saving"
							@click="review('Rejected')"
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
