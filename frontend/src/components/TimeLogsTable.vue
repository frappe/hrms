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
			<!-- plain div instead of ion-content — ion-content body is blank in this Ionic version -->
			<div class="overflow-y-auto flex flex-col gap-4 p-4 bg-white h-full">
				<div class="flex flex-col gap-1">
					<label class="text-sm text-gray-600">{{ __("Activity Type") }}</label>
					<input
						v-model="newLog.activity_type"
						type="text"
						class="border rounded p-2 text-sm w-full"
						:placeholder="__('e.g. Development')"
					/>
				</div>
				<div class="flex flex-col gap-1">
					<label class="text-sm text-gray-600">{{ __("From Time") }}</label>
					<input
						v-model="newLog.from_time"
						type="datetime-local"
						class="border rounded p-2 text-sm w-full"
						@change="calcHours"
					/>
				</div>
				<div class="flex flex-col gap-1">
					<label class="text-sm text-gray-600">{{ __("To Time") }}</label>
					<input
						v-model="newLog.to_time"
						type="datetime-local"
						class="border rounded p-2 text-sm w-full"
						@change="calcHours"
					/>
				</div>
				<div class="flex flex-col gap-1">
					<label class="text-sm text-gray-600">{{ __("Hours") }}</label>
					<input
						v-model="newLog.hours"
						type="number"
						step="0.25"
						min="0"
						class="border rounded p-2 text-sm w-full"
						:placeholder="__('Calculated automatically')"
					/>
				</div>
				<div class="flex flex-col gap-1">
					<label class="text-sm text-gray-600">{{ __("Project") }}</label>
					<input
						v-model="newLog.project"
						type="text"
						class="border rounded p-2 text-sm w-full"
						:placeholder="__('Optional')"
					/>
				</div>
				<div class="flex flex-col gap-1">
					<label class="text-sm text-gray-600">{{ __("Description") }}</label>
					<textarea
						v-model="newLog.description"
						rows="3"
						class="border rounded p-2 text-sm w-full"
						:placeholder="__('What did you work on?')"
					/>
				</div>
				<button
					class="w-full bg-blue-500 text-white rounded p-3 text-sm font-medium mt-2"
					@click="saveLog"
				>
					{{ __("Add") }}
				</button>
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
import { FeatherIcon } from "frappe-ui"

const __ = inject("$translate")
const dayjs = inject("$dayjs")

const props = defineProps({
	timesheet: { type: Object, required: true },
	isReadOnly: { type: Boolean, default: false },
})

const emit = defineEmits(["update:timesheet", "addLog", "updateLog", "deleteLog"])

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
