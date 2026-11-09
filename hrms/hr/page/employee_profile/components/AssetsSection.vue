<script setup>
import { computed, ref } from "vue";
import { Badge, Button, Dialog } from "frappe-ui";
import CardEditor from "./CardEditor.vue";
import DetailCard from "./DetailCard.vue";
import ListRow from "./ListRow.vue";
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
});
const emit = defineEmits(["saved"]);

const __ = window.__;
const frappe = window.frappe;

// the open or approved return request of each asset that has one
const returning = computed(
	() =>
		new Map(
			props.requests.filter((r) => r.request_type === "Return").map((r) => [r.asset, r]),
		),
);
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

const requesting = ref(false);
const returning_asset = ref(null);
const saving = ref(false);

async function send(values) {
	saving.value = true;
	try {
		emit("saved", await frappe.xcall(`${API}.request_asset`, { values }));
		requesting.value = false;
		returning_asset.value = null;
	} catch {
		// the server's message is already on screen
	} finally {
		saving.value = false;
	}
}

// the request the user is acting on: withdrawing their own, which stays as Cancelled, or, for HR,
// approving or rejecting it
const busy = ref(null);

async function act(request, status) {
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
				  }),
		);
	} catch {
		// the server's message is already on screen
	} finally {
		busy.value = null;
	}
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
				<div v-if="can_edit && !requesting" class="ml-auto">
					<Button
						variant="ghost"
						icon-left="lucide-plus"
						:label="__('Request asset')"
						@click="requesting = true"
					/>
				</div>
			</div>
			<div
				v-if="assets.length"
				class="flex flex-col gap-px rounded-6 border border-outline-gray-1 p-1"
			>
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
					</template>
					<template v-if="returning.get(asset.name)" #badge>
						<Badge v-bind="request_badge(returning.get(asset.name))" />
					</template>
					<template #actions>
						<template v-if="returning.get(asset.name)">
							<template
								v-if="returning.get(asset.name).status === 'Open' && can_review"
							>
								<Button
									:label="__('Reject')"
									:loading="
										busy === `${returning.get(asset.name).name}:Rejected`
									"
									@click="act(returning.get(asset.name), 'Rejected')"
								/>
								<Button
									variant="solid"
									:label="__('Approve')"
									:loading="
										busy === `${returning.get(asset.name).name}:Approved`
									"
									@click="act(returning.get(asset.name), 'Approved')"
								/>
							</template>
							<Button
								v-else-if="
									returning.get(asset.name).status === 'Approved' && can_review
								"
								:label="__('Take back')"
								@click="hand_over(returning.get(asset.name))"
							/>
							<Button
								v-else-if="returning.get(asset.name).status === 'Open' && can_edit"
								variant="ghost"
								:label="__('Withdraw')"
								:loading="busy === `${returning.get(asset.name).name}:Cancelled`"
								@click="act(returning.get(asset.name), 'Cancelled')"
							/>
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

		<DetailCard v-if="requesting" :title="__('Request an asset')">
			<CardEditor
				:fields="ISSUE_FIELDS"
				:save_label="__('Send to HR')"
				:saving="saving"
				@save="(values) => send({ request_type: 'Issue', ...values })"
				@cancel="requesting = false"
			/>
		</DetailCard>

		<section v-if="asked_for.length">
			<div class="mb-2 flex min-h-8 items-center">
				<h2 class="text-base-semibold text-ink-gray-9">{{ __("Requested") }}</h2>
			</div>
			<div class="flex flex-col gap-px rounded-6 border border-outline-gray-1 p-1">
				<ListRow v-for="request in asked_for" :key="request.name" icon="lucide-package">
					{{ request.asset_category }}
					<template #details>
						<div class="mt-0.5 truncate text-sm text-ink-gray-5">
							{{ request_line(request) }}
						</div>
					</template>
					<template #badge>
						<Badge v-bind="request_badge(request)" />
					</template>
					<template #actions>
						<template v-if="request.status === 'Open' && can_review">
							<Button
								:label="__('Reject')"
								:loading="busy === `${request.name}:Rejected`"
								@click="act(request, 'Rejected')"
							/>
							<Button
								variant="solid"
								:label="__('Approve')"
								:loading="busy === `${request.name}:Approved`"
								@click="act(request, 'Approved')"
							/>
						</template>
						<Button
							v-else-if="request.status === 'Approved' && can_review"
							:label="__('Hand over')"
							@click="hand_over(request)"
						/>
						<Button
							v-else-if="request.status === 'Open' && can_edit"
							variant="ghost"
							:label="__('Withdraw')"
							:loading="busy === `${request.name}:Cancelled`"
							@click="act(request, 'Cancelled')"
						/>
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
			@update:model-value="(open) => !open && (returning_asset = null)"
		>
			<CardEditor
				v-if="returning_asset"
				:fields="RETURN_FIELDS"
				:save_label="__('Send to HR')"
				:saving="saving"
				@save="
					(values) =>
						send({ request_type: 'Return', asset: returning_asset.name, ...values })
				"
				@cancel="returning_asset = null"
			/>
		</Dialog>
	</div>
</template>
