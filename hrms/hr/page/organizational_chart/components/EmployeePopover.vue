<script setup>
import { computed } from "vue";
import { Avatar, Badge, Button, Tooltip } from "frappe-ui";
import { leave_label } from "../utils.js";
import PersonHoverCard from "./PersonHoverCard.vue";

const props = defineProps({
	node: { type: Object, required: true },
	company: { type: String, required: true },
	is_me: { type: Boolean, default: false },
	team_open: { type: Boolean, default: false },
});

const emit = defineEmits(["close", "show_manager", "toggle_team"]);

const frappe = window.frappe;
const __ = window.__;

const on_leave = computed(() => leave_label(props.node.leave));
const reports = computed(() =>
	props.node.reports === 1 ? __("1 report") : __("{0} reports", [props.node.reports]),
);
// the manager of someone at the top of the chart can be in another company
const manager_company = computed(() =>
	props.node.manager?.company !== props.company ? props.node.manager?.company : null,
);

function open_profile() {
	frappe.set_route("Form", "Employee", props.node.id);
}

// desk's composer keeps the email on the employee's timeline. Without permission, the mail app opens.
function compose_email() {
	new frappe.views.CommunicationComposer({
		doc: { doctype: "Employee", name: props.node.id },
		recipients: props.node.email,
	});
}
</script>

<template>
	<div class="w-72 rounded-6 border border-outline-gray-2 bg-surface-base p-4 shadow-lg">
		<div class="flex items-start gap-3">
			<Avatar :image="node.image" :label="node.name" size="2xl" class="shrink-0" />
			<div class="min-w-0 flex-1">
				<div class="flex items-center gap-2">
					<span class="truncate text-base-semibold text-ink-gray-9">{{
						node.name
					}}</span>
					<span v-if="is_me" class="shrink-0 text-sm text-ink-gray-5">{{
						__("You")
					}}</span>
				</div>
				<div v-if="node.designation" class="mt-0.5 truncate text-sm text-ink-gray-6">
					{{ node.designation }}
				</div>
			</div>
			<Button
				variant="ghost"
				icon="lucide-x"
				class="-mr-1.5 -mt-1.5"
				:aria-label="__('Close')"
				@click="emit('close')"
			/>
		</div>

		<Badge v-if="on_leave" theme="blue" class="mt-3" :label="on_leave">
			<template #prefix>
				<span class="lucide-tree-palm size-3" aria-hidden="true" />
			</template>
		</Badge>

		<dl class="mt-3 space-y-1.5 text-base">
			<div v-if="node.department" class="flex items-center gap-2">
				<dt
					class="lucide-building-2 size-4 shrink-0 text-ink-gray-5"
					:aria-label="__('Department')"
				/>
				<dd class="min-w-0 truncate text-ink-gray-7">{{ node.department }}</dd>
			</div>
			<div v-if="node.branch" class="flex items-center gap-2">
				<dt
					class="lucide-map-pin size-4 shrink-0 text-ink-gray-5"
					:aria-label="__('Branch')"
				/>
				<dd class="min-w-0 truncate text-ink-gray-7">{{ node.branch }}</dd>
			</div>
			<div v-if="node.reports" class="flex items-center gap-2">
				<dt
					class="lucide-users size-4 shrink-0 text-ink-gray-5"
					:aria-label="__('Reports')"
				/>
				<dd class="min-w-0 truncate text-ink-gray-7">{{ reports }}</dd>
			</div>
			<div v-if="node.manager" class="flex items-center gap-2">
				<dt
					class="lucide-arrow-up-right size-4 shrink-0 text-ink-gray-5"
					:aria-label="__('Reports to')"
				/>
				<dd class="min-w-0 truncate text-ink-gray-7">
					<PersonHoverCard :person="node.manager">
						<button
							type="button"
							class="inline-flex min-w-0 max-w-full items-center gap-2 align-middle"
							@click="emit('show_manager', node.manager)"
						>
							<Avatar
								:image="node.manager.image"
								:label="node.manager.name"
								size="xs"
								class="shrink-0"
							/>
							<span
								class="truncate text-base text-ink-gray-8 decoration-outline-gray-3 underline-offset-2 hover:underline"
							>
								{{ node.manager.name }}
							</span>
							<span v-if="manager_company" class="shrink-0 text-ink-gray-5">
								· {{ manager_company }}
							</span>
						</button>
					</PersonHoverCard>
				</dd>
			</div>
		</dl>

		<div class="mt-4 flex items-center gap-2">
			<Button
				v-if="node.can_open"
				class="flex-1"
				:label="__('Open profile')"
				@click="open_profile"
			/>
			<!-- a disabled button takes no pointer events, so the span carries the tooltip -->
			<Tooltip v-else :text="__('You do not have access to this profile')">
				<span class="flex flex-1">
					<Button class="w-full" :label="__('Open profile')" disabled />
				</span>
			</Tooltip>
			<Tooltip v-if="node.email" :text="__('Email')">
				<Button
					v-if="node.can_email"
					icon="lucide-mail"
					:aria-label="__('Email {0}', [node.name])"
					@click="compose_email"
				/>
				<Button
					v-else
					icon="lucide-mail"
					:href="`mailto:${node.email}`"
					:aria-label="__('Email {0}', [node.name])"
				/>
			</Tooltip>
			<Tooltip v-if="node.reports" :text="team_open ? __('Hide team') : __('Show team')">
				<Button
					icon="lucide-git-fork"
					:aria-label="team_open ? __('Hide team') : __('Show team')"
					:aria-pressed="team_open"
					@click="emit('toggle_team')"
				/>
			</Tooltip>
		</div>
	</div>
</template>
