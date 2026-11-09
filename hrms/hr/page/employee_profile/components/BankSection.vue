<script setup>
import { computed, ref } from "vue";
import { Badge, Button, Dialog } from "frappe-ui";
import CardEditor from "./CardEditor.vue";
import DetailCard from "./DetailCard.vue";
import PropertyRow from "./PropertyRow.vue";
import Steps from "./Steps.vue";
import { API, short_date } from "../utils.js";

// The salary account. The employee asks HR to change it, with proof, and HR approves the request,
// which then updates it. HR changes another employee's account directly.
const props = defineProps({
	employee: { type: String, required: true },
	bank: { type: Object, required: true },
	// the open Bank Details Change Request, if any
	request: { type: Object, default: null },
	// the employee's own: they request a change
	can_edit: { type: Boolean, default: false },
	// HR's, on someone else's: they change the account directly
	can_manage: { type: Boolean, default: false },
	can_review: { type: Boolean, default: false },
	has_ifsc: { type: Boolean, default: false },
});
const emit = defineEmits(["saved"]);

const __ = window.__;
const frappe = window.frappe;

const account_rows = (account) => [
	{ label: __("Bank"), icon: "lucide-landmark", value: account.bank_name },
	{ label: __("Account number"), icon: "lucide-hash", value: account.bank_ac_no },
	props.has_ifsc
		? { label: __("IFSC"), icon: "lucide-git-branch", value: account.ifsc_code }
		: { label: __("IBAN"), icon: "lucide-globe", value: account.iban },
];
const has_account = computed(() => Boolean(props.bank.bank_ac_no));

const FIELDS = computed(() => [
	{
		fieldname: "bank_name",
		label: __("Bank"),
		icon: "lucide-landmark",
		type: "data",
		reqd: true,
	},
	{
		fieldname: "bank_ac_no",
		label: __("Account number"),
		icon: "lucide-hash",
		type: "data",
		reqd: true,
	},
	props.has_ifsc
		? { fieldname: "ifsc_code", label: __("IFSC"), icon: "lucide-git-branch", type: "data" }
		: { fieldname: "iban", label: __("IBAN"), icon: "lucide-globe", type: "data" },
	{
		fieldname: "proof",
		label: __("Proof"),
		icon: "lucide-file-check",
		type: "file",
		reqd: true,
		description: __("A cancelled cheque or a bank statement of this account"),
	},
	{ fieldname: "reason", label: __("Reason"), icon: "lucide-message-square", type: "text" },
]);

// HR keys in the account they were given; the profile shows only the end of the number in use
const DIRECT_FIELDS = computed(() => [
	{ ...FIELDS.value[0] },
	{
		...FIELDS.value[1],
		placeholder: props.bank.bank_ac_no ? __("Replaces {0}", [props.bank.bank_ac_no]) : null,
	},
	{ ...FIELDS.value[2] },
]);
const direct_values = computed(() => ({
	bank_name: props.bank.bank_name,
	ifsc_code: props.bank.ifsc_code,
}));

const editing = ref(false);
const saving = ref(false);

// HR has to accept the request, so it waits for the server, unlike the personal details
async function send(values) {
	saving.value = true;
	try {
		emit(
			"saved",
			props.can_manage
				? await frappe.xcall(`${API}.save_details`, { values, employee: props.employee })
				: await frappe.xcall(`${API}.request_bank_details_change`, { values }),
		);
		editing.value = false;
	} catch {
		// the server's message is already on screen
	} finally {
		saving.value = false;
	}
}

// what was asked for and why, with the proof HR checks
const request_rows = computed(() => [
	...account_rows(props.request).map((row, index) =>
		index === 0 ? { ...row, label: __("New bank") } : row,
	),
	{ label: __("Reason"), icon: "lucide-message-square", value: props.request.reason },
	{
		label: __("Proof"),
		icon: "lucide-file-check",
		value: props.request.proof_name || props.request.proof,
		href: props.request.proof,
	},
]);

const account_line = (account) => `${account.bank_name} ${account.bank_ac_no}`;

// The proof comes with the request, so the request waits on HR from the start
const request_steps = computed(() => [
	{
		label: __("Change requested"),
		sub: has_account.value
			? __("{0} replaces {1}", [account_line(props.request), account_line(props.bank)])
			: account_line(props.request),
		when: short_date(props.request.creation),
		state: "done",
	},
	{
		label: __("Proof added"),
		sub: props.request.proof_name,
		when: short_date(props.request.creation),
		state: "done",
	},
	{
		label: __("HR verifies the new account"),
		sub: __("HR checks the proof before approving"),
		state: "current",
	},
	{
		label: __("Salary moves to the new account"),
		sub: __("From the first payroll after HR approves"),
		state: "todo",
	},
]);

// what the open request's dialog confirms: the employee cancelling it, or HR deciding it
const confirming = ref(null);
const deciding = ref(false);
const CONFIRM = computed(() => ({
	cancel: {
		title: __("Cancel this change?"),
		text: has_account.value
			? __("Your salary keeps going to {0}. You can request a change again later.", [
					account_line(props.bank),
			  ])
			: __("You can add your bank details again later."),
		keep: __("Keep request"),
		label: __("Cancel change"),
		theme: "red",
	},
	Approved: {
		title: __("Approve this change?"),
		text: props.request
			? __("Salary goes to {0} from the next payroll.", [account_line(props.request)])
			: "",
		keep: __("Not yet"),
		label: __("Approve"),
		theme: "gray",
	},
	Rejected: {
		title: __("Reject this change?"),
		text: has_account.value
			? __("Salary keeps going to {0}.", [account_line(props.bank)])
			: __("The employee can send their bank details again."),
		keep: __("Not yet"),
		label: __("Reject"),
		theme: "red",
	},
}));

// a cancelled request stays, as Cancelled, and a new one can be raised
async function decide() {
	const name = props.request.name;
	const doctype = "Bank Details Change Request";
	deciding.value = true;
	try {
		emit(
			"saved",
			confirming.value === "cancel"
				? await frappe.xcall(`${API}.withdraw_request`, { doctype, name })
				: await frappe.xcall(`${API}.review_request`, {
						doctype,
						name,
						status: confirming.value,
				  }),
		);
	} catch {
		// the server's message is already on screen
	} finally {
		deciding.value = false;
		confirming.value = null;
	}
}
</script>

<template>
	<div class="space-y-12">
		<div>
			<!-- with no account yet, its card is where the first one is written; a new account
			shows next to the one in use, which stays until HR approves the change -->
			<DetailCard :title="__('Salary account')" :rows="account_rows(bank)">
				<template v-if="can_manage && !request && !editing" #actions>
					<Button
						variant="ghost"
						:icon-left="has_account ? 'lucide-pencil' : 'lucide-plus'"
						:label="has_account ? __('Edit') : __('Add bank details')"
						@click="editing = true"
					/>
				</template>
				<template v-else-if="can_edit && !request && !editing" #actions>
					<Button
						variant="ghost"
						:icon-left="has_account ? 'lucide-pencil' : 'lucide-plus'"
						:label="has_account ? __('Request change') : __('Add bank details')"
						@click="editing = true"
					/>
				</template>
				<template v-if="editing && can_manage" #default>
					<CardEditor
						:fields="DIRECT_FIELDS"
						:values="direct_values"
						:saving="saving"
						@save="send"
						@cancel="editing = false"
					/>
				</template>
				<template v-else-if="editing && !has_account" #default>
					<CardEditor
						:fields="FIELDS"
						:save_label="__('Send to HR')"
						:saving="saving"
						@save="send"
						@cancel="editing = false"
					/>
				</template>
			</DetailCard>
			<p class="mt-3 text-sm text-ink-gray-5">
				{{
					can_edit
						? __(
								"Your salary is paid into this account. A new account is used once HR approves it.",
						  )
						: __("Salary is paid into this account.")
				}}
			</p>
		</div>

		<DetailCard v-if="editing && has_account && !can_manage" :title="__('New account')">
			<CardEditor
				:fields="FIELDS"
				:save_label="__('Send to HR')"
				:saving="saving"
				@save="send"
				@cancel="editing = false"
			/>
		</DetailCard>

		<section v-if="request">
			<div class="mb-2 flex min-h-8 items-center gap-2">
				<h2 class="text-base-semibold text-ink-gray-9">{{ __("Account change") }}</h2>
				<Badge class="ml-auto" theme="blue" :label="__('In review')" />
			</div>
			<div class="rounded-5 border border-outline-gray-1">
				<div class="border-b border-outline-gray-1 px-4 py-2">
					<PropertyRow v-for="row in request_rows" :key="row.label" v-bind="row" />
				</div>
				<div class="p-4">
					<Steps :steps="request_steps" />
				</div>
				<div
					v-if="can_edit || can_review"
					class="flex flex-wrap items-center justify-end gap-2 border-t border-outline-gray-1 px-4 py-3"
				>
					<Button
						v-if="can_edit"
						variant="ghost"
						theme="red"
						:label="__('Cancel change')"
						@click="confirming = 'cancel'"
					/>
					<template v-if="can_review">
						<Button :label="__('Reject')" @click="confirming = 'Rejected'" />
						<Button
							variant="solid"
							icon-left="lucide-check"
							:label="__('Approve')"
							@click="confirming = 'Approved'"
						/>
					</template>
				</div>
			</div>
		</section>

		<Dialog
			v-if="request"
			:model-value="Boolean(confirming)"
			:title="confirming ? CONFIRM[confirming].title : ''"
			@update:model-value="(open) => !open && (confirming = null)"
		>
			<p v-if="confirming" class="text-p-base text-ink-gray-7">
				{{ CONFIRM[confirming].text }}
			</p>
			<template #actions>
				<div v-if="confirming" class="flex justify-end gap-2">
					<Button :label="CONFIRM[confirming].keep" @click="confirming = null" />
					<Button
						variant="solid"
						:theme="CONFIRM[confirming].theme"
						:label="CONFIRM[confirming].label"
						:loading="deciding"
						@click="decide"
					/>
				</div>
			</template>
		</Dialog>
	</div>
</template>
