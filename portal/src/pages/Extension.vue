<template>
	<PageBody :loading="screen.loading && !spec">
		<template v-if="spec">
			<PageHead :title="spec.title" :subtitle="spec.subtitle">
				<template v-if="spec.actions?.length" #actions>
					<!--
						Header actions carry the page's editable state, so an action can
						live up here while the control it commits sits in a card below.
						`field`/`current` let it disable itself until something changes.
					-->
					<Button
						v-for="a in spec.actions"
						:key="a.action"
						:variant="a.variant || 'subtle'"
						:icon-left="a.icon"
						:label="a.label"
						:loading="busy === a.action"
						:disabled="a.field ? choices[a.field] === a.current : false"
						@click="run(a.action, { ...choices, ...forms })"
					/>
				</template>
			</PageHead>

			<component
				:is="section.width === 'full' ? 'div' : 'div'"
				v-for="(section, i) in spec.sections || []"
				:key="i"
			>
				<!-- stats: the headline numbers for the screen -->
				<StatTiles v-if="section.type === 'stats'" :tiles="section.tiles || []" />

				<!-- fields: a read-only label/value list -->
				<SectionCard
					v-else-if="section.type === 'fields'"
					:title="section.title"
					:readonly-label="section.note"
				>
					<dl class="flex flex-col">
						<FieldRow
							v-for="row in section.rows || []"
							:key="row.label"
							:label="row.label"
							:value="row.value"
							:locked="row.locked"
							:nums="row.nums"
						/>
					</dl>
				</SectionCard>

				<!-- table: rows the owning app has already formatted -->
				<SectionCard
					v-else-if="section.type === 'table'"
					:title="section.title"
					:padded="false"
				>
					<DataTable
						:columns="section.columns || []"
						:rows="section.rows || []"
						:id-key="section.idKey || 'name'"
						:empty-message="section.empty || 'Nothing here yet.'"
					/>
					<TotalRow
						v-if="section.total"
						:label="section.total.label"
						:value="section.total.value"
					/>
				</SectionCard>

				<!-- files: something to view or download, e.g. a statutory PDF -->
				<SectionCard
					v-else-if="section.type === 'files'"
					:title="section.title"
					:padded="false"
				>
					<ul v-if="section.files?.length">
						<li
							v-for="f in section.files"
							:key="f.label"
							class="flex items-center justify-between gap-3 border-b border-outline-gray-1 px-3.5 py-2.5 last:border-0"
						>
							<div class="min-w-0">
								<div class="truncate text-p-base text-ink-gray-8">
									{{ f.label }}
								</div>
								<div class="truncate text-base text-ink-gray-5">{{ f.hint }}</div>
							</div>
							<div class="flex shrink-0 items-center gap-2">
								<StatusBadge v-if="f.status" :status="f.status" />
								<Button
									v-if="f.url"
									variant="ghost"
									icon="lucide-eye"
									:label="`View ${f.label}`"
									@click="openFile(f.url)"
								/>
								<Button
									v-if="f.url"
									variant="ghost"
									icon="lucide-download"
									:label="`Download ${f.label}`"
									@click="saveFile(f)"
								/>
							</div>
						</li>
					</ul>
					<div v-else class="px-3.5 pb-3.5">
						<EmptyState :message="section.empty || 'Nothing available yet.'" />
					</div>
				</SectionCard>

				<!-- note: a short callout the owning app wants to state plainly -->
				<div
					v-else-if="section.type === 'note'"
					class="rounded-6 border px-3.5 py-2.5 text-p-base"
					:class="
						section.tone === 'success'
							? 'border-outline-green-2 bg-surface-green-1 text-ink-green-3'
							: 'border-outline-gray-2 bg-surface-gray-1 text-ink-gray-7'
					"
				>
					{{ section.text }}
				</div>

				<!-- choice: pick one option, then confirm -->
				<SectionCard v-else-if="section.type === 'choice'" :title="section.title">
					<p v-if="section.hint" class="text-base text-ink-gray-5">{{ section.hint }}</p>
					<div class="grid gap-3 sm:grid-cols-2">
						<button
							v-for="opt in section.options || []"
							:key="opt.value"
							type="button"
							class="flex flex-col items-start gap-1 rounded-6 border p-3 text-left transition-colors"
							:class="
								choices[section.field] === opt.value
									? 'border-outline-gray-4 bg-surface-gray-2'
									: 'border-outline-gray-1 hover:bg-surface-gray-1'
							"
							@click="choices[section.field] = opt.value"
						>
							<span class="text-base-semibold text-ink-gray-9">{{ opt.label }}</span>
							<span class="text-base text-ink-gray-5">{{ opt.hint }}</span>
						</button>
					</div>
					<Button
						v-if="section.action"
						class="self-start"
						:variant="section.action.variant || 'subtle'"
						:label="section.action.label"
						:loading="busy === section.action.action"
						:disabled="choices[section.field] === section.current"
						@click="
							run(section.action.action, { [section.field]: choices[section.field] })
						"
					/>
				</SectionCard>

				<!-- form: editable values the owning app defines -->
				<SectionCard v-else-if="section.type === 'form'" :title="section.title">
					<p v-if="section.hint" class="text-base text-ink-gray-5">{{ section.hint }}</p>
					<div class="grid gap-3 sm:grid-cols-2">
						<RequestField
							v-for="f in section.fields || []"
							:key="f.fieldname"
							v-model="forms[f.fieldname]"
							:field="f"
							:class="f.full && 'sm:col-span-2'"
						/>
					</div>
					<Button
						v-if="section.action"
						class="self-start"
						:variant="section.action.variant || 'subtle'"
						:label="section.action.label"
						:loading="busy === section.action.action"
						@click="run(section.action.action, forms)"
					/>
				</SectionCard>
			</component>
		</template>
	</PageBody>
</template>

<script setup>
/**
 * Renders a screen contributed by another app. This file knows nothing about
 * what it is drawing: the owning app returns a spec of section types, and the
 * only thing shared between the two is that vocabulary.
 */
import { computed, reactive, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { Button, createResource } from "frappe-ui";

import PageBody from "@/components/PageBody.vue";
import PageHead from "@/components/PageHead.vue";
import SectionCard from "@/components/SectionCard.vue";
import StatTiles from "@/components/StatTiles.vue";
import StatusBadge from "@/components/StatusBadge.vue";
import DataTable from "@/components/DataTable.vue";
import FieldRow from "@/components/FieldRow.vue";
import TotalRow from "@/components/TotalRow.vue";
import EmptyState from "@/components/EmptyState.vue";
import RequestField from "@/components/RequestField.vue";

import { errorMessage, notifyError, notifySuccess } from "@/utils/toast";

const route = useRoute();
const busy = ref("");
const choices = reactive({});
const forms = reactive({});

const screen = createResource({ url: "hrms.api.portal_extensions.get_screen" });
const spec = computed(() => screen.data);

function seed(s) {
	for (const section of s?.sections || []) {
		if (section.type === "choice") choices[section.field] = section.current;
		if (section.type === "form") {
			for (const f of section.fields || []) forms[f.fieldname] = f.value ?? "";
		}
	}
}

function load() {
	screen.fetch({ slug: route.params.slug }).then(seed);
}
watch(() => route.params.slug, load, { immediate: true });

async function run(action, values) {
	busy.value = action;
	try {
		const res = await fetch("/api/method/hrms.api.portal_extensions.run_action", {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
				Accept: "application/json",
				"X-Frappe-CSRF-Token": window.csrf_token,
			},
			body: JSON.stringify({ slug: route.params.slug, action, values: values || {} }),
		});
		if (!res.ok) throw new Error(await res.text());
		const out = (await res.json()).message || {};
		if (out.file) saveFile(out.file);
		if (out.spec) {
			screen.data = out.spec;
			seed(out.spec);
		}
		notifySuccess(out.message || "Done");
	} catch (e) {
		notifyError("Could not complete", errorMessage(e, "Try again in a moment."));
	} finally {
		busy.value = "";
	}
}

function openFile(url) {
	window.open(url, "_blank", "noopener");
}

async function saveFile(file) {
	try {
		const res = await fetch(file.url);
		if (!res.ok) throw new Error(await res.text());
		const href = URL.createObjectURL(await res.blob());
		const a = document.createElement("a");
		a.href = href;
		a.download = file.filename || `${file.label}.pdf`;
		a.click();
		URL.revokeObjectURL(href);
	} catch (e) {
		notifyError("Could not download", errorMessage(e, "Try again in a moment."));
	}
}
</script>
