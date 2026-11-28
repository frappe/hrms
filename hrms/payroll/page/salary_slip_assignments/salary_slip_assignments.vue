<script setup>
import { computed, onMounted } from "vue";

const props = defineProps({
	route: { type: Array, default: () => [] },
	query: { type: Object, default: () => ({}) },
	// In the Salary Slip form, the Vue Component field passes the document
	doctype: { type: String, default: null },
	name: { type: String, default: null },
	doc: { type: Object, default: null },
	read_only: { type: Boolean, default: true },
});
const emit = defineEmits(["title"]);

const frappe = window.frappe;
const __ = window.__;

const in_form = computed(() => props.doctype === "Salary Slip");
const periods = computed(() => props.doc?.__onload?.salary_structure_assignment_periods || []);

const format_date = (value) => frappe.datetime.str_to_user(value);
const format_days = (value) => frappe.format(value || 0, { fieldtype: "Float" }, { inline: true });
const format_amount = (value) => window.format_currency(value, props.doc?.currency);
const assignment_link = (name) => frappe.utils.get_form_link("Salary Structure Assignment", name);

const total = (fieldname) =>
	periods.value.reduce((sum, period) => sum + (period[fieldname] || 0), 0);

onMounted(() => {
	if (!in_form.value) emit("title", __("Salary Slip Assignments"));
});
</script>

<template>
	<div v-if="!in_form" class="p-5 text-base text-ink-gray-5">
		{{
			__("Open a Salary Slip to see the Salary Structure Assignments it is calculated from.")
		}}
	</div>
	<div v-else-if="periods.length" class="flex flex-col gap-2">
		<div class="text-base-semibold text-ink-gray-9">
			{{ __("Salary Structure Assignments") }}
		</div>
		<p class="text-p-sm text-ink-gray-5">
			{{
				__(
					"Each assignment pays for its own dates. Its days are counted with the same Payroll Settings as the whole slip.",
				)
			}}
		</p>
		<div class="overflow-x-auto rounded-5 border border-outline-gray-1">
			<table class="w-full text-base">
				<thead>
					<tr class="bg-surface-gray-2 text-left text-sm text-ink-gray-5">
						<th class="px-3 py-2 font-medium">{{ __("Assignment") }}</th>
						<th class="px-3 py-2 font-medium">{{ __("Salary Structure") }}</th>
						<th class="px-3 py-2 font-medium">{{ __("From Date") }}</th>
						<th class="px-3 py-2 font-medium">{{ __("To Date") }}</th>
						<th class="px-3 py-2 text-right font-medium">{{ __("Base") }}</th>
						<th class="px-3 py-2 text-right font-medium">{{ __("Working Days") }}</th>
						<th class="px-3 py-2 text-right font-medium">
							{{ __("Leave Without Pay") }}
						</th>
						<th class="px-3 py-2 text-right font-medium">{{ __("Absent Days") }}</th>
						<th class="px-3 py-2 text-right font-medium">{{ __("Payment Days") }}</th>
					</tr>
				</thead>
				<tbody class="tabular-nums text-ink-gray-8">
					<tr
						v-for="period in periods"
						:key="period.salary_structure_assignment"
						class="border-t border-outline-gray-1"
					>
						<td class="whitespace-nowrap px-3 py-2">
							<a
								:href="assignment_link(period.salary_structure_assignment)"
								class="hover:underline"
							>
								{{ period.salary_structure_assignment }}
							</a>
						</td>
						<td class="whitespace-nowrap px-3 py-2">{{ period.salary_structure }}</td>
						<td class="whitespace-nowrap px-3 py-2">
							{{ format_date(period.from_date) }}
						</td>
						<td class="whitespace-nowrap px-3 py-2">
							{{ format_date(period.to_date) }}
						</td>
						<td class="whitespace-nowrap px-3 py-2 text-right">
							{{ format_amount(period.base) }}
						</td>
						<td class="px-3 py-2 text-right">
							{{ format_days(period.total_working_days) }}
						</td>
						<td class="px-3 py-2 text-right">
							{{ format_days(period.leave_without_pay) }}
						</td>
						<td class="px-3 py-2 text-right">{{ format_days(period.absent_days) }}</td>
						<td class="px-3 py-2 text-right">
							{{ format_days(period.payment_days) }}
						</td>
					</tr>
					<tr class="border-t border-outline-gray-1 font-medium">
						<td class="px-3 py-2" colspan="5">{{ __("Total") }}</td>
						<td class="px-3 py-2 text-right">
							{{ format_days(total("total_working_days")) }}
						</td>
						<td class="px-3 py-2 text-right">
							{{ format_days(total("leave_without_pay")) }}
						</td>
						<td class="px-3 py-2 text-right">
							{{ format_days(total("absent_days")) }}
						</td>
						<td class="px-3 py-2 text-right">
							{{ format_days(total("payment_days")) }}
						</td>
					</tr>
				</tbody>
			</table>
		</div>
	</div>
</template>
