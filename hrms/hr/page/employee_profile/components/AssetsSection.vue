<script setup>
import { computed, nextTick, ref } from "vue";
import { Badge, Button, Dialog, Textarea } from "frappe-ui";
import CardEditor from "./CardEditor.vue";
import ListRow, { LIST_CLASS } from "./ListRow.vue";
import PropertyRow from "./PropertyRow.vue";
import { API, short_date } from "../utils.js";

// What the employee holds, as ERPNext's assets record it, and their requests to HR for an asset or
// to return one. HR approves a request and then makes the Asset Movement from it, which hands the
// asset over or takes it back.
const props = defineProps({
	assets: { type: Array, default: () => [] },
	// open Asset Requests, and approved ones waiting for their Asset Movement
	requests: { type: Array, default: () => [] },
	asset_categories: { type: Array, default: () => [] },
	// the employee's own
	can_edit: { type: Boolean, default: false },
	can_review: { type: Boolean, default: false },
	// HR's, on someone else's: they give an asset directly, with an Asset Movement
	can_assign: { type: Boolean, default: false },
	employee: { type: String, default: null },
	company: { type: String, default: null },
});
const emit = defineEmits(["saved"]);

const __ = window.__;
const frappe = window.frappe;

// the return request of each asset that has one: the open or approved one, else the one rejected
// lately, as the server lists them in that order
const returning = computed(() => {
	const map = new Map();
	for (const request of props.requests) {
		if (request.request_type === "Return" && !map.has(request.asset)) {
			map.set(request.asset, request);
		}
	}
	return map;
});
// a return that is still under way; after a rejection the employee can ask again
const is_returning = (asset) => {
	const request = returning.value.get(asset.name);
	return request && request.status !== "Rejected";
};
const asked_for = computed(() => props.requests.filter((r) => r.request_type === "Issue"));

const ISSUE_FIELDS = computed(() => [
	{
		fieldname: "asset_category",
		label: __("Asset"),
		icon: "lucide-laptop",
		type: "select",
		options: props.asset_categories,
		reqd: true,
	},
	{
		fieldname: "required_by",
		label: __("Needed by"),
		icon: "lucide-calendar",
		type: "date",
		min: frappe.datetime.get_today(),
		max: null,
	},
	{ fieldname: "reason", label: __("Reason"), icon: "lucide-message-square", type: "text" },
]);
const RETURN_FIELDS = [
	{ fieldname: "reason", label: __("Reason"), icon: "lucide-message-square", type: "text" },
];

// the asking form: a new request ({}), or the employee's open one, which they change until HR
// decides it
const requesting = ref(null);
// the asset being given back, and its open return request when that is being changed
const returning_asset = ref(null);
const return_request = ref(null);
const saving = ref(false);

function close_return() {
	returning_asset.value = null;
	return_request.value = null;
}

async function send(values, name = null) {
	saving.value = true;
	try {
		emit("saved", await frappe.xcall(`${API}.request_asset`, { values, name }));
		if (values.request_type === "Issue") requesting.value = null;
		else close_return();
	} catch {
		// the server's message is already on screen
	} finally {
		saving.value = false;
	}
}

// HR reviews an open request: what was asked for and why, then approves or rejects it
const reviewing = ref(null);
// Reject first asks why, in place of the request's details, so a note is never typed for an
// approval and lost
const rejection = ref({ open: false, reason: "", error: null });
const reason_input = ref(null);

async function ask_reason() {
	rejection.value.open = true;
	await nextTick();
	reason_input.value?.focus();
}
const review_rows = computed(() => {
	const request = reviewing.value;
	if (!request) return [];
	const asset = props.assets.find((asset) => asset.name === request.asset);
	return [
		request.request_type === "Issue"
			? { label: __("Asset"), icon: "lucide-laptop", value: request.asset_category }
			: {
					label: __("Return"),
					icon: "lucide-laptop",
					value: asset?.asset_name || request.asset_name || request.asset,
			  },
		request.request_type === "Issue" && {
			label: __("Needed by"),
			icon: "lucide-calendar",
			value: short_date(request.required_by),
		},
		{ label: __("Reason"), icon: "lucide-message-square", value: request.reason },
		{
			label: __("Request"),
			icon: "lucide-file-text",
			value: request.name,
			href: frappe.utils.get_form_link("Asset Request", request.name),
		},
	].filter(Boolean);
});

function start_review(request) {
	rejection.value = { open: false, reason: "", error: null };
	reviewing.value = request;
}

// a rejection says why, so the employee knows what to do next
async function decide(status) {
	const reason = rejection.value.reason.trim();
	if (status === "Rejected" && !reason) {
		rejection.value.error = __("Say why, so they know what to do next");
		return;
	}
	if (await act(reviewing.value, status, status === "Rejected" ? reason : null)) {
		reviewing.value = null;
	}
}

// the request the user is acting on: withdrawing their own, which is discarded and stays as
// Cancelled, or, for HR,
// approving or rejecting it
const busy = ref(null);

async function act(request, status, reason = null) {
	busy.value = `${request.name}:${status}`;
	try {
		emit(
			"saved",
			status === "Cancelled"
				? await frappe.xcall(`${API}.withdraw_request`, {
						doctype: "Asset Request",
						name: request.name,
				  })
				: await frappe.xcall(`${API}.review_request`, {
						doctype: "Asset Request",
						name: request.name,
						status,
						reason,
				  }),
		);
		return true;
	} catch {
		// the server's message is already on screen
	} finally {
		busy.value = null;
	}
}

// HR gives an asset without a request: a new Asset Movement that issues it to the employee
function assign() {
	frappe.model.with_doctype("Asset Movement", () => {
		const movement = frappe.model.get_new_doc("Asset Movement");
		movement.purpose = "Issue";
		movement.company = props.company;
		frappe.model.add_child(movement, "assets").to_employee = props.employee;
		frappe.set_route("Form", "Asset Movement", movement.name);
	});
}

// HR carries out an approved request with an Asset Movement, made from the request
function hand_over(request) {
	if (request.asset_movement) {
		frappe.set_route("Form", "Asset Movement", request.asset_movement);
		return;
	}
	frappe.model.open_mapped_doc({
		method: "hrms.hr.doctype.asset_request.asset_request.make_asset_movement",
		source_name: request.name,
	});
}

function request_badge(request) {
	if (request.status === "Rejected") {
		return {
			theme: "red",
			label: request.request_type === "Issue" ? __("Rejected") : __("Return rejected"),
		};
	}
	if (request.status === "Approved") {
		return {
			theme: "green",
			label: request.request_type === "Issue" ? __("Approved") : __("Return approved"),
		};
	}
	return {
		theme: "amber",
		label: request.request_type === "Issue" ? __("Pending") : __("Return requested"),
	};
}

function request_line(request) {
	if (request.status === "Rejected") {
		return __("Rejected on {0}", [short_date(request.modified)]);
	}
	if (request.status === "Approved") {
		return request.request_type === "Issue"
			? __("HR hands it over next")
			: __("Hand it back to HR");
	}
	return request.required_by
		? __("Asked on {0}, needed by {1}", [
				short_date(request.creation),
				short_date(request.required_by),
		  ])
		: __("Asked on {0}", [short_date(request.creation)]);
}
</script>

<template>
	<div class="space-y-12">
		<section>
			<div class="mb-2 flex min-h-8 items-center gap-2">
				<h2 class="text-base-semibold text-ink-gray-9">{{ __("Assets") }}</h2>
				<Badge v-if="assets.length" theme="gray" :label="String(assets.length)" />
				<div v-if="can_edit" class="ml-auto">
					<Button
						variant="ghost"
						icon-left="lucide-plus"
						:label="__('Request asset')"
						@click="requesting = {}"
					/>
				</div>
				<div v-else-if="can_assign" class="ml-auto">
					<Button
						variant="ghost"
						icon-left="lucide-plus"
						:label="__('Assign asset')"
						@click="assign"
					/>
				</div>
			</div>
			<div v-if="assets.length" :class="LIST_CLASS">
				<ListRow v-for="asset in assets" :key="asset.name" icon="lucide-laptop">
					{{ asset.asset_name || asset.item_name }}
					<template #details>
						<div
							class="mt-0.5 flex flex-wrap items-center gap-x-4 gap-y-0.5 text-sm text-ink-gray-5"
						>
							<span class="flex items-center gap-1.5 whitespace-nowrap">
								<span class="lucide-tag size-3.5" />{{ asset.name }}
							</span>
							<span
								v-if="asset.since"
								class="flex items-center gap-1.5 whitespace-nowrap"
							>
								<span class="lucide-calendar size-3.5" />
								{{ __("Since {0}", [short_date(asset.since)]) }}
							</span>
						</div>
						<div
							v-if="returning.get(asset.name)"
							class="mt-0.5 truncate text-sm text-ink-gray-5"
						>
							{{ request_line(returning.get(asset.name)) }}
						</div>
						<div
							v-if="returning.get(asset.name)?.rejection_reason"
							class="mt-0.5 break-words text-sm text-ink-red-7"
						>
							{{ returning.get(asset.name).rejection_reason }}
						</div>
					</template>
					<template v-if="returning.get(asset.name)" #badge>
						<Badge v-bind="request_badge(returning.get(asset.name))" />
					</template>
					<template #actions>
						<template v-if="is_returning(asset)">
							<Button
								v-if="returning.get(asset.name).status === 'Open' && can_review"
								:label="__('Review')"
								@click="start_review(returning.get(asset.name))"
							/>
							<Button
								v-else-if="
									returning.get(asset.name).status === 'Approved' && can_review
								"
								:label="__('Take back')"
								@click="hand_over(returning.get(asset.name))"
							/>
							<template
								v-else-if="returning.get(asset.name).status === 'Open' && can_edit"
							>
								<Button
									variant="ghost"
									:label="__('Withdraw')"
									:loading="
										busy === `${returning.get(asset.name).name}:Cancelled`
									"
									@click="act(returning.get(asset.name), 'Cancelled')"
								/>
								<Button
									variant="ghost"
									icon="lucide-pencil"
									:tooltip="__('Edit')"
									:aria-label="
										__('Edit return of {0}', [asset.asset_name || asset.name])
									"
									@click="
										returning_asset = asset;
										return_request = returning.get(asset.name);
									"
								/>
							</template>
						</template>
						<Button
							v-else-if="can_edit"
							variant="ghost"
							:label="__('Return')"
							@click="returning_asset = asset"
						/>
					</template>
				</ListRow>
			</div>
			<p v-else class="text-base text-ink-gray-6">{{ __("No assets assigned") }}</p>
		</section>

		<!-- a dialog, so the form shows where the user is, also on a phone; not closed by a click
		outside, as reka-ui takes a click on the date picker inside the page's shadow root for one -->
		<Dialog
			v-if="can_edit"
			:model-value="Boolean(requesting)"
			:title="requesting?.name ? __('Change request') : __('Request an asset')"
			:dismissible="false"
			@update:model-value="(open) => !open && (requesting = null)"
		>
			<CardEditor
				v-if="requesting"
				:key="requesting.name || 'new'"
				:fields="ISSUE_FIELDS"
				:values="requesting"
				:save_label="__('Send to HR')"
				:saving="saving"
				@save="(values) => send({ request_type: 'Issue', ...values }, requesting.name)"
				@cancel="requesting = null"
			/>
		</Dialog>

		<section v-if="asked_for.length">
			<div class="mb-2 flex min-h-8 items-center">
				<h2 class="text-base-semibold text-ink-gray-9">{{ __("Requested") }}</h2>
			</div>
			<div :class="LIST_CLASS">
				<ListRow v-for="request in asked_for" :key="request.name" icon="lucide-package">
					{{ request.asset_category }}
					<template #details>
						<div class="mt-0.5 truncate text-sm text-ink-gray-5">
							{{ request_line(request) }}
						</div>
						<div
							v-if="request.rejection_reason"
							class="mt-0.5 break-words text-sm text-ink-red-7"
						>
							{{ request.rejection_reason }}
						</div>
					</template>
					<template #badge>
						<Badge v-bind="request_badge(request)" />
					</template>
					<template #actions>
						<Button
							v-if="request.status === 'Open' && can_review"
							:label="__('Review')"
							@click="start_review(request)"
						/>
						<Button
							v-else-if="request.status === 'Approved' && can_review"
							:label="__('Hand over')"
							@click="hand_over(request)"
						/>
						<template v-else-if="request.status === 'Open' && can_edit">
							<Button
								variant="ghost"
								:label="__('Withdraw')"
								:loading="busy === `${request.name}:Cancelled`"
								@click="act(request, 'Cancelled')"
							/>
							<Button
								variant="ghost"
								icon="lucide-pencil"
								:tooltip="__('Edit')"
								:aria-label="__('Edit request for {0}', [request.asset_category])"
								@click="requesting = request"
							/>
						</template>
					</template>
				</ListRow>
			</div>
		</section>

		<Dialog
			v-if="can_edit"
			:model-value="Boolean(returning_asset)"
			:title="
				returning_asset
					? __('Return {0}', [returning_asset.asset_name || returning_asset.name])
					: ''
			"
			@update:model-value="(open) => !open && close_return()"
		>
			<CardEditor
				v-if="returning_asset"
				:fields="RETURN_FIELDS"
				:values="return_request || {}"
				:save_label="__('Send to HR')"
				:saving="saving"
				@save="
					(values) =>
						send(
							{ request_type: 'Return', asset: returning_asset.name, ...values },
							return_request?.name,
						)
				"
				@cancel="close_return"
			/>
		</Dialog>

		<Dialog
			v-if="can_review"
			:model-value="Boolean(reviewing)"
			:title="
				reviewing?.request_type === 'Return'
					? __('Review return request')
					: __('Review asset request')
			"
			@update:model-value="(open) => !open && (reviewing = null)"
		>
			<div v-if="reviewing">
				<PropertyRow v-for="row in review_rows" :key="row.label" v-bind="row" />
				<p class="mt-2 text-sm text-ink-gray-5">
					{{ __("Asked on {0}", [short_date(reviewing.creation)]) }}
				</p>
				<div v-if="rejection.open" class="mt-3">
					<Textarea
						ref="reason_input"
						v-model="rejection.reason"
						:label="__('Why is it rejected?')"
						:rows="3"
						:placeholder="__('The employee sees this')"
						:error="rejection.error"
					/>
				</div>
			</div>
			<template #actions>
				<div v-if="reviewing && rejection.open" class="flex justify-end gap-2">
					<Button :label="__('Back')" @click="rejection.open = false" />
					<Button
						variant="solid"
						theme="red"
						:label="__('Reject')"
						:loading="busy === `${reviewing.name}:Rejected`"
						@click="decide('Rejected')"
					/>
				</div>
				<div v-else-if="reviewing" class="flex justify-end gap-2">
					<Button :label="__('Reject')" @click="ask_reason" />
					<Button
						variant="solid"
						icon-left="lucide-check"
						:label="__('Approve')"
						:loading="busy === `${reviewing.name}:Approved`"
						@click="decide('Approved')"
					/>
				</div>
			</template>
		</Dialog>
	</div>
</template>
