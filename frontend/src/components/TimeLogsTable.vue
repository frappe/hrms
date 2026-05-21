<template>
	<div class="flex flex-col gap-3 mt-2">
		<!-- Existing rows -->
		<div
			v-if="timesheet.time_logs?.length"
			class="flex flex-col bg-white rounded border overflow-hidden"
		>
			<div
				v-for="(log, idx) in timesheet.time_logs"
				:key="idx"
				class="flex flex-row items-center justify-between p-3.5"
				:class="idx !== timesheet.time_logs.length - 1 && 'border-b'"
			>
				<div class="flex flex-col gap-1 grow">
					<div class="flex flex-row items-center justify-between">
						<span class="text-sm font-medium text-gray-800">
							{{ log.activity_type || __("No Activity") }}
						</span>
						<span class="text-sm font-semibold text-gray-700">
							{{ log.hours ? log.hours + " hrs" : "" }}
						</span>
					</div>
					<div class="text-xs text-gray-500 flex flex-row gap-2">
						<span v-if="log.from_time">{{ formatTime(log.from_time) }}</span>
						<span v-if="log.from_time && log.to_time">→</span>
						<span v-if="log.to_time">{{ formatTime(log.to_time) }}</span>
						<span v-if="log.project" class="ml-1 text-gray-400">· {{ log.project }}</span>
					</div>
					<div v-if="log.description" class="text-xs text-gray-400 truncate">
						{{ log.description }}
					</div>
				</div>
				<button
					v-if="!isReadOnly"
					class="ml-3 text-gray-400 hover:text-red-500"
					@click="$emit('deleteLog', idx)"
				>
					<FeatherIcon name="trash-2" class="h-4 w-4" />
				</button>
			</div>
		</div>

		<!-- Add row button -->
		<button
			v-if="!isReadOnly"
			class="flex flex-row items-center gap-2 text-sm text-blue-500 font-medium py-2"
			@click="showModal = true"
		>
			<FeatherIcon name="plus" class="h-4 w-4" />
			{{ __("Add Time Log") }}
		</button>

		<!-- Add modal -->
		<ion-modal :is-open="showModal" @did-dismiss="closeModal">
			<ion-header>
				<ion-toolbar>
					<ion-title>{{ __("Add Time Log") }}</ion-title>
					<ion-buttons slot="end">
						<ion-button @click="closeModal">{{ __("Cancel") }}</ion-button>
					</ion-buttons>
				</ion-toolbar>
			</ion-header>
			<!-- plain div — ion-content body is blank in this Ionic version -->
			<div class="overflow-y-auto flex flex-col gap-4 p-4 bg-white h-full">
				<FormField
					v-for="field in LOG_FIELDS"
					:key="field.fieldname"
					:label="__(field.label)"
					:fieldtype="field.fieldtype"
					:fieldname="field.fieldname"
					:options="field.options"
					:placeholder="field.placeholder"
					v-model="newLog[field.fieldname]"
					@change="field.fieldname === 'from_time' || field.fieldname === 'to_time' ? calcHours() : null"
				/>
				<Button
					variant="solid"
					class="w-full mt-2"
					@click="saveLog"
				>
					{{ __("Add") }}
				</Button>
			</div>
		</ion-modal>
	</div>
</template>

<script setup>
import { ref, inject } from "vue"
import {
	IonModal, IonHeader, IonToolbar, IonTitle,
	IonButtons, IonButton,
} from "@ionic/vue"
import { FeatherIcon, Button } from "frappe-ui"
import FormField from "@/components/FormField.vue"

const __ = inject("$translate")
const dayjs = inject("$dayjs")

const props = defineProps({
	timesheet: { type: Object, required: true },
	isReadOnly: { type: Boolean, default: false },
})

const emit = defineEmits(["update:timesheet", "addLog", "updateLog", "deleteLog"])

const LOG_FIELDS = [
	{
		fieldname: "activity_type",
		fieldtype: "Link",
		label: "Activity Type",
		options: "Activity Type",
	},
	{
		fieldname: "from_time",
		fieldtype: "Datetime",
		label: "From Time",
	},
	{
		fieldname: "to_time",
		fieldtype: "Datetime",
		label: "To Time",
	},
	{
		fieldname: "hours",
		fieldtype: "Float",
		label: "Hours",
		placeholder: "Calculated automatically",
	},
	{
		fieldname: "project",
		fieldtype: "Link",
		label: "Project",
		options: "Project",
	},
	{
		fieldname: "description",
		fieldtype: "Small Text",
		label: "Description",
	},
]

const showModal = ref(false)
const newLog = ref({})

function closeModal() {
	showModal.value = false
	newLog.value = {}
}

function calcHours() {
	if (newLog.value.from_time && newLog.value.to_time) {
		const diff = dayjs(newLog.value.to_time).diff(dayjs(newLog.value.from_time), "minute")
		if (diff > 0) newLog.value.hours = parseFloat((diff / 60).toFixed(2))
	}
}

function saveLog() {
	if (!newLog.value.hours && !newLog.value.from_time) return
	emit("addLog", { ...newLog.value })
	closeModal()
}

function formatTime(dt) {
	if (!dt) return ""
	return dayjs(dt).format("HH:mm")
}
</script>
