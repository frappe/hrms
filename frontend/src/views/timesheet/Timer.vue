<template>
	<ion-page>
		<ion-content :fullscreen="true">
			<div class="flex flex-col min-h-full bg-gray-50">
				<!-- Header -->
				<header
					class="flex items-center bg-white shadow-sm px-3 py-4 sticky top-0 z-10 gap-1"
				>
					<Button variant="ghost" class="!pl-0 hover:bg-white" @click="router.back()">
						<FeatherIcon name="chevron-left" class="h-5 w-5" />
					</Button>
					<h1 class="text-xl font-semibold text-gray-900">{{ __("Time Tracker") }}</h1>
				</header>

				<!-- Timer display -->
				<div
					class="flex flex-col items-center justify-center py-10 bg-white mx-4 mt-4 rounded-xl shadow-sm border"
				>
					<div
						class="text-6xl font-mono font-bold tracking-widest tabular-nums"
						:class="isRunning ? 'text-gray-900' : 'text-gray-400'"
					>
						{{ formattedTime }}
					</div>
					<div
						v-if="isRunning"
						class="mt-3 flex items-center gap-2 text-sm text-green-600 font-medium"
					>
						<span class="h-2 w-2 rounded-full bg-green-500 animate-pulse"></span>
						{{ __("Recording…") }}
					</div>
					<div v-else-if="elapsed > 0" class="mt-3 text-sm text-gray-400">
						{{ __("Stopped") }}
					</div>
					<div v-else class="mt-3 text-sm text-gray-400">
						{{ __("Press Start to begin tracking") }}
					</div>
				</div>

				<!-- Form fields -->
				<div class="flex flex-col gap-4 p-4 bg-white mx-4 mt-3 rounded-xl shadow-sm border">
					<FormField
						fieldtype="Link"
						fieldname="activity_type"
						:label="__('Activity Type')"
						options="Activity Type"
						v-model="form.activity_type"
						@change="persistState"
					/>
					<FormField
						fieldtype="Link"
						fieldname="project"
						:label="__('Project')"
						options="Project"
						v-model="form.project"
						@change="persistState"
					/>
					<FormField
						fieldtype="Small Text"
						fieldname="description"
						:label="__('Description')"
						v-model="form.description"
						@change="persistState"
					/>
				</div>

				<!-- Action buttons -->
				<div class="px-4 mt-4 pb-10 flex flex-col gap-3">
					<!-- Start button (idle state) -->
					<button
						v-if="!isRunning"
						@click="start"
						class="w-full py-5 rounded-xl bg-green-500 active:bg-green-600 text-white font-semibold text-lg flex items-center justify-center gap-2 shadow-sm transition-colors"
					>
						<FeatherIcon name="play" class="h-5 w-5" />
						{{ __("Start Timer") }}
					</button>

					<!-- Stop & Save button (running state) -->
					<button
						v-else
						@click="stop"
						:disabled="isSaving"
						class="w-full py-5 rounded-xl bg-red-500 active:bg-red-600 text-white font-semibold text-lg flex items-center justify-center gap-2 shadow-sm transition-colors disabled:opacity-60"
					>
						<FeatherIcon name="square" class="h-5 w-5" />
						{{ isSaving ? __("Saving…") : __("Stop & Save") }}
					</button>

					<!-- Discard (running state) -->
					<button
						v-if="isRunning"
						@click="discard"
						class="w-full py-3 text-sm text-red-400 font-medium"
					>
						{{ __("Discard") }}
					</button>
				</div>
			</div>
		</ion-content>
	</ion-page>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, inject } from "vue"
import { useRouter } from "vue-router"
import { IonPage, IonContent } from "@ionic/vue"
import { FeatherIcon, Button, call, toast } from "frappe-ui"
import FormField from "@/components/FormField.vue"

const router = useRouter()
const __ = inject("$translate")
const employee = inject("$employee")
const dayjs = inject("$dayjs")

const STORAGE_KEY = "hrms_active_timer"

const isRunning = ref(false)
const startTime = ref(null)   // dayjs-compatible string
const elapsed = ref(0)        // seconds since start
const isSaving = ref(false)
const form = ref({ activity_type: "", project: "", description: "" })

let ticker = null

// ─── Computed ────────────────────────────────────────────────────────────────

const formattedTime = computed(() => {
	const h = Math.floor(elapsed.value / 3600).toString().padStart(2, "0")
	const m = Math.floor((elapsed.value % 3600) / 60).toString().padStart(2, "0")
	const s = (elapsed.value % 60).toString().padStart(2, "0")
	return `${h}:${m}:${s}`
})

// ─── Persistence ─────────────────────────────────────────────────────────────

function persistState() {
	if (!isRunning.value) return
	localStorage.setItem(
		STORAGE_KEY,
		JSON.stringify({ startTime: startTime.value, form: form.value }),
	)
}

function clearPersistedState() {
	localStorage.removeItem(STORAGE_KEY)
}

function loadPersistedState() {
	try {
		const raw = localStorage.getItem(STORAGE_KEY)
		if (!raw) return
		const state = JSON.parse(raw)
		if (!state.startTime) return

		startTime.value = state.startTime
		form.value = state.form || { activity_type: "", project: "", description: "" }
		elapsed.value = Math.floor(
			(Date.now() - new Date(state.startTime).getTime()) / 1000,
		)
		isRunning.value = true
		startTick()
	} catch {
		clearPersistedState()
	}
}

// ─── Timer control ───────────────────────────────────────────────────────────

function startTick() {
	ticker = setInterval(() => {
		elapsed.value = Math.floor(
			(Date.now() - new Date(startTime.value).getTime()) / 1000,
		)
	}, 1000)
}

function start() {
	startTime.value = new Date().toISOString()
	elapsed.value = 0
	isRunning.value = true
	startTick()
	persistState()
}

async function stop() {
	if (!startTime.value || isSaving.value) return
	clearInterval(ticker)
	ticker = null
	isSaving.value = true

	const fromTime = dayjs(startTime.value).format("YYYY-MM-DD HH:mm:ss")
	const toTime = dayjs().format("YYYY-MM-DD HH:mm:ss")
	const hours = parseFloat((elapsed.value / 3600).toFixed(4))

	try {
		const name = await call("hrms.api.save_timer_log", {
			employee: employee.data.name,
			from_time: fromTime,
			to_time: toTime,
			hours,
			activity_type: form.value.activity_type || null,
			project: form.value.project || null,
			description: form.value.description || null,
		})

		clearPersistedState()
		isRunning.value = false
		startTime.value = null
		elapsed.value = 0
		form.value = { activity_type: "", project: "", description: "" }

		toast({
			title: __("Time log saved!"),
			icon: "check",
			iconClasses: "text-green-500",
		})

		// Navigate to the timesheet that was created/updated
		router.push({ name: "TimesheetDetailView", params: { id: name } })
	} catch (e) {
		// Resume the ticker so the timer doesn't lose time
		startTick()
		toast({
			title: __("Failed to save time log"),
			icon: "x",
			iconClasses: "text-red-500",
		})
	} finally {
		isSaving.value = false
	}
}

function discard() {
	clearInterval(ticker)
	ticker = null
	clearPersistedState()
	isRunning.value = false
	startTime.value = null
	elapsed.value = 0
}

// ─── Lifecycle ───────────────────────────────────────────────────────────────

onMounted(() => loadPersistedState())
onUnmounted(() => clearInterval(ticker))
</script>
