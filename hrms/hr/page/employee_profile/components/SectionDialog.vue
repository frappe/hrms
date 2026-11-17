<script setup>
import { ref, watch } from "vue";
import { Badge, Button, Dialog, FileUploader, TextInput, Textarea } from "frappe-ui";

// One section being edited: a copy, handed back on Done, so Close leaves it as it was
const props = defineProps({
	section: { type: Object, default: null },
	first: { type: Boolean, default: false },
	last: { type: Boolean, default: false },
	// what to write, for the sections suggested under "Ideas for your profile"
	placeholder: { type: String, default: null },
});
const open = defineModel("open", { type: Boolean, default: false });
const emit = defineEmits(["done", "move", "remove"]);

const __ = window.__;
const PLACEHOLDERS = {
	Text: __("Where you worked before, what you care about, life outside work."),
	Tags: __("e.g. payroll, Figma, chess"),
};

const draft = ref(null);
const new_tag = ref("");

watch(
	() => [open.value, props.section],
	() => {
		if (open.value && props.section) {
			draft.value = JSON.parse(JSON.stringify(props.section));
			new_tag.value = "";
		}
	},
	{ immediate: true },
);

// "payroll, Figma" adds two topics, as the placeholder shows
function add_tag() {
	for (const tag of new_tag.value.split(",").map((tag) => tag.trim())) {
		if (tag && !draft.value.content.includes(tag)) draft.value.content.push(tag);
	}
	new_tag.value = "";
}

// what is typed but not added yet, and links without a URL, before the section is saved
function tidy() {
	if (draft.value.type === "Tags") add_tag();
	if (draft.value.type === "Links") {
		draft.value.content = draft.value.content.filter((link) => link.url?.trim());
	}
	return JSON.parse(JSON.stringify(draft.value));
}

function done() {
	emit("done", tidy());
	open.value = false;
}
</script>

<template>
	<Dialog v-model="open" :title="__('Edit {0}', [section?.title || __('section')])">
		<template #default>
			<div v-if="draft" class="flex flex-col gap-4">
				<TextInput v-model="draft.title" :label="__('Title')" />

				<Textarea
					v-if="draft.type === 'Text'"
					v-model="draft.content"
					:label="__('Text')"
					:placeholder="placeholder || PLACEHOLDERS.Text"
					:rows="8"
				/>

				<div v-else-if="draft.type === 'Tags'" class="flex flex-col gap-2">
					<div class="flex items-end gap-2">
						<TextInput
							v-model="new_tag"
							class="flex-1"
							:label="__('Add a topic')"
							:placeholder="PLACEHOLDERS.Tags"
							@keydown.enter.prevent="add_tag"
						/>
						<Button :label="__('Add')" :disabled="!new_tag.trim()" @click="add_tag" />
					</div>
					<!-- frappe-ui's removable tag: a Badge with its remove control in #suffix -->
					<div class="flex flex-wrap gap-1.5">
						<Badge
							v-for="(tag, index) in draft.content"
							:key="tag"
							theme="gray"
							size="md"
						>
							{{ tag }}
							<template #suffix>
								<span
									role="button"
									tabindex="0"
									class="-mr-0.5 inline-flex cursor-pointer items-center justify-center rounded-1 p-0.5 opacity-70 hover:opacity-100"
									:aria-label="__('Remove {0}', [tag])"
									@click="draft.content.splice(index, 1)"
									@keydown.enter="draft.content.splice(index, 1)"
								>
									<span class="lucide-x size-3" />
								</span>
							</template>
						</Badge>
					</div>
				</div>

				<div v-else-if="draft.type === 'Links'" class="flex flex-col gap-2">
					<div
						v-for="(link, index) in draft.content"
						:key="index"
						class="flex items-end gap-2"
					>
						<TextInput
							v-model="link.title"
							class="flex-1"
							:placeholder="__('Link {0} title', [index + 1])"
						/>
						<TextInput
							v-model="link.url"
							class="flex-1"
							:placeholder="__('Link {0} URL', [index + 1])"
						/>
						<Button
							variant="ghost"
							icon="lucide-x"
							:aria-label="__('Remove link')"
							@click="draft.content.splice(index, 1)"
						/>
					</div>
					<Button
						class="self-start"
						icon-left="lucide-plus"
						:label="__('Add link')"
						@click="draft.content.push({ title: '', url: '', note: '' })"
					/>
				</div>

				<div v-else-if="draft.type === 'Photos'" class="flex flex-col gap-3">
					<div class="grid grid-cols-2 gap-3">
						<div
							v-for="(photo, index) in draft.content"
							:key="photo.image"
							class="flex flex-col gap-1.5"
						>
							<div
								class="relative aspect-video overflow-hidden rounded-4 bg-surface-gray-2"
							>
								<img :src="photo.image" alt="" class="size-full object-cover" />
								<Button
									class="absolute right-1 top-1"
									icon="lucide-x"
									:aria-label="__('Remove photo')"
									@click="draft.content.splice(index, 1)"
								/>
							</div>
							<TextInput v-model="photo.caption" :placeholder="__('Caption')" />
						</div>
					</div>
					<FileUploader
						v-if="draft.content.length < 12"
						:file-types="['image/*']"
						:private="false"
						optimize
						@success="
							(file) => draft.content.push({ image: file.file_url, caption: '' })
						"
					>
						<template #default="{ openFileSelector, uploading, progress }">
							<Button
								class="self-start"
								icon-left="lucide-image-plus"
								:loading="uploading"
								:label="
									uploading ? __('Uploading {0}%', [progress]) : __('Add photo')
								"
								@click="openFileSelector"
							/>
						</template>
					</FileUploader>
				</div>
			</div>
		</template>

		<template #actions>
			<div class="flex items-center gap-1">
				<Button
					variant="ghost"
					icon="lucide-arrow-up"
					:aria-label="__('Move up')"
					:disabled="first"
					@click="emit('move', -1, tidy())"
				/>
				<Button
					variant="ghost"
					icon="lucide-arrow-down"
					:aria-label="__('Move down')"
					:disabled="last"
					@click="emit('move', 1, tidy())"
				/>
				<Button
					variant="ghost"
					theme="red"
					:label="__('Remove')"
					@click="
						emit('remove');
						open = false;
					"
				/>
				<Button class="ml-auto" variant="solid" :label="__('Done')" @click="done" />
			</div>
		</template>
	</Dialog>
</template>
