<template>
	<div class="w-full flex flex-col gap-4">
		<!-- Header row: title + period selector -->
		<div class="flex items-center justify-between">
			<h2 class="text-base font-semibold text-gray-800">{{ __("Working Hours") }}</h2>
			<div class="flex rounded-lg overflow-hidden border border-gray-200">
				<button
					v-for="opt in PERIODS"
					:key="opt.value"
					@click="selectPeriod(opt.value)"
					class="px-3 py-1.5 text-xs font-medium transition-colors"
					:class="
						period === opt.value
							? 'bg-gray-800 text-white'
							: 'bg-white text-gray-500 hover:bg-gray-50'
					"
				>
					{{ opt.label }}
				</button>
			</div>
		</div>

		<!-- Hours card -->
		<div class="bg-white rounded-xl border p-4">
			<!-- Loading -->
			<div v-if="hoursResource.loading" class="h-32 flex items-center justify-center">
				<LoadingIndicator class="h-5 w-5 text-gray-400" />
			</div>

			<template v-else>
				<!-- Total -->
				<div class="mb-4 flex items-baseline gap-2">
					<span class="text-4xl font-bold text-gray-900 tabular-nums">
						{{ hoursData.total ?? 0 }}
					</span>
					<span class="text-sm text-gray-500">{{ __("hours") }}</span>
					<span class="text-xs text-gray-400 ml-auto">{{ periodLabel }}</span>
				</div>

				<!-- Bar chart -->
				<div v-if="hasHours" class="flex flex-col gap-1.5">
					<div class="flex items-end gap-0.5" style="height: 80px">
						<div
							v-for="day in hoursData.daily"
							:key="day.date"
							class="flex-1 rounded-t transition-all duration-300 cursor-default"
							:class="
								isToday(day.date)
									? 'bg-blue-600'
									: day.hours > 0
									? 'bg-blue-400 hover:bg-blue-500'
									: 'bg-gray-100'
							"
							:style="{ height: `${barHeight(day.hours)}%` }"
							:title="`${formatDateFull(day.date)}: ${day.hours}h`"
						/>
					</div>
					<!-- X labels -->
					<div class="flex gap-0.5">
						<div
							v-for="(day, idx) in hoursData.daily"
							:key="day.date"
							class="flex-1 text-center"
						>
							<span
								v-if="showXLabel(idx)"
								class="text-[9px] leading-none"
								:class="isToday(day.date) ? 'text-blue-600 font-semibold' : 'text-gray-400'"
							>
								{{ xLabel(day.date) }}
							</span>
						</div>
					</div>
				</div>

				<p v-else class="text-sm text-gray-400 text-center py-6">
					{{ __("No hours logged in this period") }}
				</p>
			</template>
		</div>

		<!-- Projects card -->
		<div v-if="projectData.length > 0" class="bg-white rounded-xl border p-4">
			<h3 class="text-sm font-semibold text-gray-700 mb-3">{{ __("My Projects") }}</h3>
			<div class="flex flex-col gap-3">
				<div
					v-for="proj in projectData"
					:key="proj.project"
					class="flex flex-col gap-1"
				>
					<div class="flex justify-between items-baseline gap-2">
						<span class="text-sm text-gray-700 truncate">{{ proj.project }}</span>
						<span class="text-xs font-semibold text-gray-500 shrink-0 tabular-nums">
							{{ proj.hours }}h
						</span>
					</div>
					<div class="h-1.5 w-full bg-gray-100 rounded-full overflow-hidden">
						<div
							class="h-full bg-blue-400 rounded-full transition-all duration-500"
							:style="{ width: `${Math.max((proj.hours / projectData[0].hours) * 100, 4)}%` }"
						/>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { ref, computed, inject } from "vue"
import { createResource, LoadingIndicator } from "frappe-ui"

const __ = inject("$translate")
const dayjs = inject("$dayjs")
const employee = inject("$employee")

const PERIODS = [
	{ label: "Week",  value: "week",   days: 7  },
	{ label: "2W",    value: "2weeks", days: 14 },
	{ label: "Month", value: "month",  days: 30 },
]

const period = ref("week")

const toDate   = computed(() => dayjs().format("YYYY-MM-DD"))
const fromDate = computed(() => {
	const days = PERIODS.find((p) => p.value === period.value)?.days ?? 7
	return dayjs().subtract(days - 1, "day").format("YYYY-MM-DD")
})

const periodLabel = computed(() => {
	const days = PERIODS.find((p) => p.value === period.value)?.days ?? 7
	return `last ${days} days`
})

// ─── Resources ────────────────────────────────────────────────────────────────

const hoursResource = createResource({
	url: "hrms.api.get_working_hours_summary",
	auto: false,
})

const projectResource = createResource({
	url: "hrms.api.get_employee_project_summary",
	auto: false,
})

const hoursData    = computed(() => hoursResource.data  || { daily: [], total: 0 })
const projectData  = computed(() => projectResource.data || [])
const hasHours     = computed(() => (hoursData.value.daily || []).some((d) => d.hours > 0))

// ─── Actions ──────────────────────────────────────────────────────────────────

function fetchData() {
	const params = {
		employee: employee.data.name,
		from_date: fromDate.value,
		to_date:   toDate.value,
	}
	hoursResource.submit(params)
	projectResource.submit(params)
}

function selectPeriod(value) {
	period.value = value
	fetchData()
}

// ─── Chart helpers ────────────────────────────────────────────────────────────

const maxHours = computed(() =>
	Math.max(...(hoursData.value.daily || []).map((d) => d.hours), 1)
)

function barHeight(hours) {
	if (hours === 0) return 3
	return Math.max((hours / maxHours.value) * 100, 6)
}

function isToday(date) {
	return date === toDate.value
}

function formatDateFull(date) {
	return dayjs(date).format("ddd, D MMM")
}

function showXLabel(idx) {
	const n    = hoursData.value.daily?.length ?? 7
	const step = n <= 7 ? 1 : n <= 14 ? 2 : 5
	return idx % step === 0 || idx === n - 1
}

function xLabel(date) {
	const n = hoursData.value.daily?.length ?? 7
	return n <= 14
		? dayjs(date).format("dd")[0]   // M, T, W…
		: dayjs(date).format("D")       // 1, 6, 11…
}

// ─── Init ─────────────────────────────────────────────────────────────────────

fetchData()
</script>
