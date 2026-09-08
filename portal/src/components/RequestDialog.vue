<template>
	<!-- One form for every employee-raised document; the schema comes from the server. -->
	<Dialog v-model="isOpen" :options="{ title, size: tableField ? 'lg' : 'md' }">
		<template #body-content>
			<div v-if="!schema" class="flex items-center gap-2 py-6 text-base text-ink-gray-5">
				<LoadingIndicator class="h-4 w-4" />
				Loading
			</div>

			<div v-else class="flex flex-col gap-4">
				<div v-if="flatFields.length" class="grid gap-3 sm:grid-cols-2">
					<div
						v-for="f in flatFields"
						:key="f.fieldname"
						:class="f.full && 'sm:col-span-2'"
					>
						<RequestField v-model="values[f.fieldname]" :field="f" />
					</div>
				</div>

				<!-- repeatable child rows, e.g. expense claim line items -->
				<template v-if="tableField">
					<div
						v-for="(row, i) in values[tableField.fieldname]"
						:key="i"
						class="flex flex-col gap-3 rounded-lg border border-outline-gray-2 p-3"
					>
						<div class="flex items-center justify-between">
							<span class="text-base font-medium text-ink-gray-5">
								{{ tableField.row_label }} {{ i + 1 }}
							</span>
							<Button
								v-if="values[tableField.fieldname].length > 1"
								variant="ghost"
								:aria-label="`Remove ${tableField.row_label.toLowerCase()}`"
								@click="values[tableField.fieldname].splice(i, 1)"
							>
								<template #icon
									><FeatherIcon name="trash-2" class="h-3.5 w-3.5"
								/></template>
							</Button>
						</div>
						<div class="grid gap-3 sm:grid-cols-3">
							<div
								v-for="f in tableField.fields"
								:key="f.fieldname"
								:class="f.full && 'sm:col-span-3'"
							>
								<RequestField v-model="row[f.fieldname]" :field="f" />
							</div>
						</div>
					</div>

					<Button variant="subtle" class="self-start" @click="addRow">
						<template #prefix
							><FeatherIcon name="plus" class="h-3.5 w-3.5"
						/></template>
						Add Another {{ tableField.row_label }}
					</Button>
				</template>

				<div
					v-if="schema.supports_attachments"
					class="flex flex-col gap-2 border-t border-outline-gray-1 pt-3"
				>
					<span class="text-base font-medium text-ink-gray-5">Attachments</span>

					<ul v-if="keptAttachments.length" class="flex flex-col gap-1.5">
						<li
							v-for="a in keptAttachments"
							:key="a.name"
							class="flex items-center justify-between gap-2 rounded border border-outline-gray-2 px-2 py-1.5"
						>
							<a
								:href="a.file_url"
								target="_blank"
								rel="noopener"
								class="flex min-w-0 items-center gap-2 text-p-base text-ink-gray-8 hover:underline"
							>
								<FeatherIcon
									name="paperclip"
									class="h-3.5 w-3.5 shrink-0 text-ink-gray-4"
								/>
								<span class="truncate">{{ a.file_name }}</span>
							</a>
							<Button
								class="shrink-0"
								variant="ghost"
								aria-label="Remove attachment"
								@click="removed.push(a.name)"
							>
								<template #icon
									><FeatherIcon name="x" class="h-3.5 w-3.5"
								/></template>
							</Button>
						</li>
					</ul>

					<ul v-if="files.length" class="flex flex-col gap-1.5">
						<li
							v-for="(f, i) in files"
							:key="f.name + i"
							class="flex items-center justify-between gap-2 rounded border border-outline-gray-2 px-2 py-1.5"
						>
							<div class="flex min-w-0 items-center gap-2">
								<FeatherIcon
									name="paperclip"
									class="h-3.5 w-3.5 shrink-0 text-ink-gray-4"
								/>
								<span class="truncate text-p-base text-ink-gray-8">{{
									f.name
								}}</span>
								<span class="nums shrink-0 text-base text-ink-gray-5">{{
									fileSize(f.size)
								}}</span>
							</div>
							<Button
								class="shrink-0"
								variant="ghost"
								aria-label="Remove attachment"
								@click="files.splice(i, 1)"
							>
								<template #icon
									><FeatherIcon name="x" class="h-3.5 w-3.5"
								/></template>
							</Button>
						</li>
					</ul>

					<Button variant="subtle" class="self-start" @click="fileInput.click()">
						<template #prefix
							><FeatherIcon name="paperclip" class="h-3.5 w-3.5"
						/></template>
						Attach Files
					</Button>
					<input
						ref="fileInput"
						type="file"
						multiple
						class="hidden"
						accept="image/png,image/jpeg,image/gif,.pdf,.doc,.docx,.xls,.xlsx,.txt,.csv"
						@change="addFiles"
					/>
					<p class="text-base text-ink-gray-5">
						Up to {{ MAX_FILES }} files, {{ MAX_FILE_MB }} MB each.
					</p>
				</div>

				<p class="text-base text-ink-gray-5">
					Saved as a draft. Your approver reviews and submits it.
				</p>
			</div>
		</template>

		<template #actions>
			<div class="flex items-center justify-between gap-3">
				<span v-if="total !== null" class="nums text-p-base text-ink-gray-7">
					Total {{ money(total, { currency }) }}
				</span>
				<div class="ml-auto flex gap-2">
					<Button variant="subtle" @click="close">Cancel</Button>
					<Button variant="solid" :loading="saving" :disabled="!schema" @click="save">
						{{ editing ? "Save Changes" : "Save" }}
					</Button>
				</div>
			</div>
		</template>
	</Dialog>
</template>

<script setup>
import { computed, reactive, ref, watch } from "vue";
import { Button, Dialog, FeatherIcon, LoadingIndicator } from "frappe-ui";

import RequestField from "@/components/RequestField.vue";
import { createRequest, requestForm, updateRequest } from "@/data/requests";
import { money } from "@/utils/format";
import { errorMessage, notifyError, notifySuccess } from "@/utils/toast";

const props = defineProps({
	open: Boolean,
	type: { type: String, required: true },
	// pass an existing draft to edit it, omit to create a new one
	request: { type: Object, default: null },
	currency: { type: String, default: null },
});
const emit = defineEmits(["update:open", "saved"]);

const MAX_FILES = 5;
const MAX_FILE_MB = 10;

const schema = ref(null);
const values = reactive({});
const files = ref([]);
const existing = ref([]);
const removed = ref([]);
const fileInput = ref(null);
const saving = ref(false);

const editing = computed(() => Boolean(props.request?.name));
const isOpen = computed({
	get: () => props.open,
	set: (v) => emit("update:open", v),
});

const title = computed(() => {
	const label = schema.value?.label || "Request";
	return editing.value ? `Edit ${label}` : `New ${label}`;
});

const flatFields = computed(() => (schema.value?.fields || []).filter((f) => f.type !== "table"));
const tableField = computed(() => (schema.value?.fields || []).find((f) => f.type === "table"));

const keptAttachments = computed(() =>
	existing.value.filter((a) => !removed.value.includes(a.name)),
);

/** Only shown when the child rows carry an amount, e.g. an expense claim. */
const total = computed(() => {
	const t = tableField.value;
	if (!t) return null;
	const numeric = t.fields.find((f) => f.type === "number");
	if (!numeric) return null;
	return (values[t.fieldname] || []).reduce(
		(sum, r) => sum + (Number(r[numeric.fieldname]) || 0),
		0,
	);
});

function blankRow() {
	return Object.fromEntries(
		tableField.value.fields.map((f) => [f.fieldname, f.type === "checkbox" ? false : ""]),
	);
}

function addRow() {
	values[tableField.value.fieldname].push(blankRow());
}

function seed() {
	const source = props.request?.values || {};
	for (const key of Object.keys(values)) delete values[key];

	for (const f of flatFields.value) {
		const v = source[f.fieldname];
		values[f.fieldname] = f.type === "checkbox" ? Boolean(v) : v ?? "";
	}
	if (tableField.value) {
		const rows = source[tableField.value.fieldname];
		values[tableField.value.fieldname] = rows?.length
			? rows.map((r) =>
					Object.fromEntries(
						tableField.value.fields.map((f) => [f.fieldname, r[f.fieldname] ?? ""]),
					),
			  )
			: [blankRow()];
	}
	existing.value = props.request?.attachments || [];
	files.value = [];
	removed.value = [];
}

watch(
	() => [props.open, props.type],
	async ([open]) => {
		if (!open) return;
		schema.value = await requestForm.fetch({ request_type: props.type });
		seed();
	},
	{ immediate: true },
);

function fileSize(bytes) {
	if (bytes >= 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
	return `${Math.max(1, Math.round(bytes / 1024))} KB`;
}

function addFiles(event) {
	for (const f of event.target.files) {
		if (keptAttachments.value.length + files.value.length >= MAX_FILES) {
			notifyError("Too many files", `You can attach at most ${MAX_FILES} files.`);
			break;
		}
		if (f.size > MAX_FILE_MB * 1024 * 1024) {
			notifyError("File too large", `${f.name} is over ${MAX_FILE_MB} MB.`);
			continue;
		}
		files.value.push(f);
	}
	event.target.value = "";
}

function toBase64(file) {
	return new Promise((resolve, reject) => {
		const reader = new FileReader();
		reader.onload = () => resolve(String(reader.result).split(",")[1]);
		reader.onerror = () => reject(new Error(`Could not read ${file.name}`));
		reader.readAsDataURL(file);
	});
}

function close() {
	isOpen.value = false;
}

/** Mirrors the server rules so the employee is told before a round trip. */
function firstProblem() {
	for (const f of flatFields.value) {
		if (f.required && !String(values[f.fieldname] ?? "").trim()) {
			return `${f.label} is required`;
		}
	}
	const t = tableField.value;
	if (t) {
		for (const [i, row] of (values[t.fieldname] || []).entries()) {
			for (const f of t.fields) {
				if (!f.required) continue;
				const v = row[f.fieldname];
				if (f.type === "number" ? !(Number(v) > 0) : !String(v ?? "").trim()) {
					return `${f.label} is required for ${t.row_label.toLowerCase()} ${i + 1}`;
				}
			}
		}
	}
	return null;
}

async function save() {
	const problem = firstProblem();
	if (problem) {
		notifyError("Incomplete form", problem);
		return;
	}
	saving.value = true;
	try {
		const attachments = [];
		for (const f of files.value) {
			attachments.push({ filename: f.name, content: await toBase64(f) });
		}
		const payload = {
			request_type: props.type,
			values: JSON.stringify(values),
			attachments: JSON.stringify(attachments),
		};
		if (editing.value) {
			await updateRequest.submit({
				...payload,
				name: props.request.name,
				removed_attachments: JSON.stringify(removed.value),
			});
			notifySuccess(`${schema.value.label} updated`);
		} else {
			await createRequest.submit(payload);
			notifySuccess(`${schema.value.label} saved`, "It is now with your approver.");
		}
		emit("saved");
		close();
	} catch (e) {
		notifyError("Could not save", errorMessage(e, "Try again in a moment."));
	} finally {
		saving.value = false;
	}
}
</script>
