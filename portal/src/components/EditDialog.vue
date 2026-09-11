<template>
	<Dialog v-model:open="isOpen" :title="title" :size="'md'">
		<template #default>
			<div class="flex flex-col gap-3">
				<div class="grid gap-3 sm:grid-cols-2">
					<div
						v-for="f in editable"
						:key="f.fieldname"
						:class="f.fullWidth && 'sm:col-span-2'"
					>
						<FormControl
							v-model="draft[f.fieldname]"
							:type="f.type || 'text'"
							:label="f.label"
							:options="f.options"
							:placeholder="f.placeholder"
						/>
					</div>
				</div>

				<!-- locked fields stay visible, otherwise people assume the field is missing -->
				<div v-if="locked.length" class="flex flex-col gap-2">
					<div class="grid gap-3 sm:grid-cols-2">
						<div v-for="f in locked" :key="f.fieldname" class="flex flex-col gap-1">
							<span class="text-base text-ink-gray-5">{{ f.label }}</span>
							<div
								class="flex items-center justify-between gap-2 rounded-4 border border-outline-gray-2 px-2 py-1.5 text-p-base text-ink-gray-6"
							>
								<span class="truncate">{{
									values[f.fieldname] || "Not set"
								}}</span>
								<span
									class="h-3 w-3 shrink-0 text-ink-gray-4 lucide-lock"
									aria-hidden="true"
								/>
							</div>
						</div>
					</div>
					<p class="text-base text-ink-gray-5">{{ lockedNames }} managed by HR.</p>
				</div>
			</div>
		</template>

		<template #actions>
			<div class="flex items-center justify-between gap-3">
				<span class="hidden text-base text-ink-gray-5 sm:block">
					Visible to your reporting manager
				</span>
				<div class="ml-auto flex gap-2">
					<Button variant="subtle" @click="close">Cancel</Button>
					<Button variant="solid" :loading="saving" :disabled="!dirty" @click="save">
						Save
					</Button>
				</div>
			</div>
		</template>
	</Dialog>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import { Button, Dialog, FormControl } from "frappe-ui";

import { updateProfile } from "@/data/portal";
import { errorMessage, notifyError, notifySuccess } from "@/utils/toast";

const props = defineProps({
	open: Boolean,
	title: String,
	fields: { type: Array, default: () => [] },
	values: { type: Object, default: () => ({}) },
});
const emit = defineEmits(["update:open", "saved"]);

const draft = ref({});
const saving = ref(false);

const isOpen = computed({
	get: () => props.open,
	set: (value) => emit("update:open", value),
});

const editable = computed(() => props.fields.filter((f) => !f.locked));
const locked = computed(() => props.fields.filter((f) => f.locked));
const lockedNames = computed(() => {
	const names = locked.value.map((f) => f.label);
	if (names.length === 1) return `${names[0]} is`;
	return `${names.slice(0, -1).join(", ")} and ${names.at(-1)} are`;
});

const dirty = computed(() =>
	editable.value.some(
		(f) => (draft.value[f.fieldname] ?? "") !== (props.values[f.fieldname] ?? ""),
	),
);

watch(
	() => props.open,
	(open) => {
		if (!open) return;
		draft.value = Object.fromEntries(
			editable.value.map((f) => [f.fieldname, props.values[f.fieldname] ?? ""]),
		);
	},
	{ immediate: true },
);

function close() {
	isOpen.value = false;
}

async function save() {
	saving.value = true;
	try {
		const changed = {};
		for (const f of editable.value) {
			const next = draft.value[f.fieldname] ?? "";
			if (next !== (props.values[f.fieldname] ?? "")) changed[f.fieldname] = next;
		}
		await updateProfile.submit({ values: JSON.stringify(changed) });
		notifySuccess("Profile updated");
		emit("saved");
		close();
	} catch (e) {
		notifyError("Could not save", errorMessage(e, "Try again in a moment."));
	} finally {
		saving.value = false;
	}
}
</script>
