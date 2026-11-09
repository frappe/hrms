<script setup>
import { computed, reactive, ref } from "vue";
import { Badge, Button, Dropdown, Textarea, Tooltip } from "frappe-ui";
import SectionDialog from "./SectionDialog.vue";

const props = defineProps({
	sections: { type: Array, default: () => [] },
	name: { type: String, required: true },
	can_edit: { type: Boolean, default: false },
});
// every change hands back the whole list of sections, which the page saves
const emit = defineEmits(["save"]);

const __ = window.__;

// a long text shows its first lines until "Read more": long in characters, or in short lines
const LONG_TEXT = 320;
const LONG_LINES = 6;
const opened = reactive(new Set());

const headline = computed(() => props.sections.find((section) => section.type === "Headline"));
const body = computed(() =>
	props.sections
		.map((section, index) => ({ ...section, index }))
		.filter(
			(section) =>
				!["Cover", "Headline"].includes(section.type) &&
				(props.can_edit || !is_empty(section)),
		),
);

function is_empty(section) {
	return Array.isArray(section.content) ? !section.content.length : !section.content?.trim();
}

function is_long(section) {
	return section.content.length > LONG_TEXT || section.content.split("\n").length > LONG_LINES;
}

function shown_text(section) {
	if (opened.has(section.index) || !is_long(section)) return section.content;
	const first_lines = section.content.split("\n").slice(0, LONG_LINES).join("\n");
	return `${first_lines.slice(0, LONG_TEXT).trimEnd()}…`;
}

// the headline is edited where it is shown
const headline_draft = ref(null);

function save_headline() {
	const text = headline_draft.value.trim();
	const rest = props.sections.filter((section) => section.type !== "Headline");
	emit("save", text ? [{ type: "Headline", title: "", content: text }, ...rest] : rest);
	headline_draft.value = null;
}

// the other sections in a dialog
const editing = ref(null);
// a new section stays in the dialog until Done, so closing it leaves nothing behind
const adding = ref(null);
const dialog_open = ref(false);
const dialog_section = computed(() => adding.value || props.sections[editing.value]);

function edit(index) {
	adding.value = null;
	editing.value = index;
	dialog_open.value = true;
}

function replace(section) {
	const sections = [...props.sections];
	if (adding.value) {
		sections.push(section);
		adding.value = null;
	} else {
		sections[editing.value] = section;
	}
	emit("save", sections);
}

// up or down among the sections shown below the headline, with what is typed in the dialog so far
function move(step, draft) {
	if (adding.value) return;
	const order = body.value.map((section) => section.index);
	const other = order[order.indexOf(editing.value) + step];
	if (other === undefined) return;
	const sections = [...props.sections];
	sections[editing.value] = draft;
	[sections[editing.value], sections[other]] = [sections[other], sections[editing.value]];
	editing.value = other;
	emit("save", sections);
}

function remove() {
	if (adding.value) {
		adding.value = null;
		return;
	}
	emit(
		"save",
		props.sections.filter((section, index) => index !== editing.value),
	);
}

const NEW_SECTIONS = [
	{
		label: __("Text"),
		icon: "lucide-text",
		section: { type: "Text", title: __("Currently"), content: "" },
	},
	{
		label: __("Ask me about"),
		icon: "lucide-tags",
		section: { type: "Tags", title: __("Ask me about"), content: [] },
	},
	{
		label: __("Photos"),
		icon: "lucide-image",
		section: { type: "Photos", title: __("Photos"), content: [] },
	},
	{
		label: __("Links"),
		icon: "lucide-link",
		section: { type: "Links", title: __("Things I wrote"), content: [] },
	},
];
const new_section_options = NEW_SECTIONS.map((option) => ({
	label: option.label,
	icon: option.icon,
	onClick: () => add(option.section),
}));

// text sections the person has not written yet, suggested below their profile
const IDEAS = [
	{
		title: __("About me"),
		icon: "lucide-user-round",
		prompt: __("Where you worked before, what you care about, life outside work."),
	},
	{
		title: __("How I like to work"),
		icon: "lucide-clock",
		prompt: __("Focus hours, how you prefer feedback, the best way to reach you."),
	},
	{
		title: __("Currently"),
		icon: "lucide-book-open",
		prompt: __("What you are working on, reading or learning."),
	},
];
const ideas = computed(() =>
	IDEAS.filter((idea) => !props.sections.some((section) => section.title === idea.title)),
);
const editing_prompt = computed(
	() => IDEAS.find((idea) => idea.title === dialog_section.value?.title)?.prompt,
);

function add(section) {
	editing.value = null;
	adding.value = JSON.parse(JSON.stringify(section));
	dialog_open.value = true;
}
</script>

<template>
	<div class="max-w-[40rem]">
		<div v-if="headline_draft !== null" class="flex flex-col gap-2">
			<Textarea
				v-model="headline_draft"
				:rows="3"
				:placeholder="__('One line about you, at the top of your profile')"
			/>
			<div class="flex gap-2">
				<Button variant="solid" :label="__('Save')" @click="save_headline" />
				<Button :label="__('Cancel')" @click="headline_draft = null" />
			</div>
		</div>
		<div v-else-if="headline?.content || can_edit" class="group relative">
			<p
				v-if="headline?.content"
				class="max-w-[40ch] text-3xl font-medium leading-snug text-ink-gray-9"
			>
				{{ headline.content }}
			</p>
			<Button
				v-else
				icon-left="lucide-plus"
				:label="__('Add a line about you')"
				@click="headline_draft = ''"
			/>
			<Tooltip v-if="can_edit && headline?.content" :text="__('Edit')">
				<Button
					class="absolute right-0 top-0 md:opacity-0 md:focus-visible:opacity-100 md:group-hover:opacity-100"
					variant="ghost"
					icon="lucide-pencil"
					:aria-label="__('Edit bio')"
					@click="headline_draft = headline.content"
				/>
			</Tooltip>
		</div>

		<p
			v-if="!can_edit && !body.length && !headline?.content"
			class="text-base text-ink-gray-6"
		>
			{{ __("{0} has not written anything here yet.", [name]) }}
		</p>

		<div class="space-y-10" :class="(headline?.content || can_edit) && 'mt-10'">
			<section v-for="section in body" :key="section.index" class="group">
				<div class="mb-2 flex min-h-8 items-center gap-2">
					<h2 class="text-base-semibold text-ink-gray-9">{{ section.title }}</h2>
					<div v-if="can_edit" class="ml-auto flex items-center gap-1">
						<Tooltip :text="__('Edit')">
							<Button
								class="md:opacity-0 md:focus-visible:opacity-100 md:group-hover:opacity-100"
								variant="ghost"
								:icon="
									section.type === 'Photos'
										? 'lucide-image-plus'
										: 'lucide-pencil'
								"
								:aria-label="__('Edit {0}', [section.title])"
								@click="edit(section.index)"
							/>
						</Tooltip>
					</div>
				</div>

				<p v-if="is_empty(section)" class="text-base text-ink-gray-5">
					{{ __("Nothing here yet") }}
				</p>

				<template v-else-if="section.type === 'Text'">
					<p class="whitespace-pre-line text-p-base text-ink-gray-7">
						{{ shown_text(section) }}
					</p>
					<Button
						v-if="is_long(section)"
						variant="ghost"
						class="-ml-2 mt-1"
						:label="opened.has(section.index) ? __('Show less') : __('Read more')"
						@click="
							opened.has(section.index)
								? opened.delete(section.index)
								: opened.add(section.index)
						"
					/>
				</template>

				<div v-else-if="section.type === 'Tags'" class="flex flex-wrap gap-1.5">
					<Badge v-for="tag in section.content" :key="tag" theme="gray" :label="tag" />
				</div>

				<div
					v-else-if="section.type === 'Photos'"
					class="grid grid-cols-2 gap-3 sm:grid-cols-3"
				>
					<figure v-for="photo in section.content" :key="photo.image">
						<div class="aspect-video overflow-hidden rounded-4 bg-surface-gray-2">
							<img
								:src="photo.image"
								:alt="photo.caption"
								class="size-full object-cover"
							/>
						</div>
						<figcaption
							v-if="photo.caption"
							class="mt-1.5 truncate text-sm text-ink-gray-5"
						>
							{{ photo.caption }}
						</figcaption>
					</figure>
				</div>

				<div
					v-else-if="section.type === 'Links'"
					class="flex flex-col gap-px rounded-6 border border-outline-gray-1 p-1"
				>
					<a
						v-for="link in section.content"
						:key="link.url + link.title"
						:href="link.url"
						target="_blank"
						rel="noopener noreferrer"
						class="relative flex w-full cursor-pointer items-center gap-3 rounded-4 px-3 py-2.5 text-left transition-colors before:pointer-events-none before:absolute before:inset-x-3 before:-top-px before:border-t before:border-outline-gray-1 first:before:hidden hover:bg-surface-gray-1 hover:before:opacity-0 [&:hover+*]:before:opacity-0"
					>
						<span class="lucide-link size-4 shrink-0 text-ink-gray-5" />
						<span class="min-w-0 flex-1 truncate text-base text-ink-gray-8">
							{{ link.title }}
						</span>
						<span v-if="link.note" class="shrink-0 text-sm text-ink-gray-5">
							{{ link.note }}
						</span>
						<span class="lucide-arrow-up-right size-4 shrink-0 text-ink-gray-4" />
					</a>
				</div>
			</section>
		</div>

		<div v-if="can_edit && ideas.length" class="mt-10">
			<p class="mb-2 text-sm text-ink-gray-5">{{ __("Ideas for your profile") }}</p>
			<div class="flex flex-col gap-px rounded-6 border border-outline-gray-1 p-1">
				<div
					v-for="idea in ideas"
					:key="idea.title"
					class="relative flex w-full cursor-pointer items-center gap-3 rounded-4 px-3 py-2.5 text-left transition-colors before:pointer-events-none before:absolute before:inset-x-3 before:-top-px before:border-t before:border-outline-gray-1 first:before:hidden hover:bg-surface-gray-1 hover:before:opacity-0 [&:hover+*]:before:opacity-0"
					@click="add({ type: 'Text', title: idea.title, content: '' })"
				>
					<span
						:class="idea.icon"
						class="size-4 shrink-0 text-ink-gray-5"
						aria-hidden="true"
					/>
					<span class="shrink-0 text-base text-ink-gray-8">{{ idea.title }}</span>
					<span
						class="hidden min-w-0 flex-1 truncate text-base text-ink-gray-5 sm:block"
					>
						{{ idea.prompt }}
					</span>
					<Button
						class="ml-auto shrink-0"
						variant="ghost"
						:label="__('Write')"
						@click.stop="add({ type: 'Text', title: idea.title, content: '' })"
					/>
				</div>
			</div>
		</div>

		<!-- Dropdown does not take a class, so the spacing is on a wrapper -->
		<div v-if="can_edit" :class="ideas.length ? 'mt-4' : 'mt-10'">
			<Dropdown :options="new_section_options">
				<Button icon-left="lucide-plus" :label="__('Add a section')" />
			</Dropdown>
		</div>

		<SectionDialog
			v-model:open="dialog_open"
			:section="dialog_section"
			:first="Boolean(adding) || body[0]?.index === editing"
			:last="Boolean(adding) || body[body.length - 1]?.index === editing"
			:placeholder="editing_prompt"
			@done="replace"
			@move="move"
			@remove="remove"
		/>
	</div>
</template>
