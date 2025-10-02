<template>
  <div class="h-screen overflow-hidden flex flex-col">
    <!-- Toolbar / Title row -->
    <div ref="toolbarRef" class="px-12 py-8 pb-4">
      <div class="flex items-center">
        <FeatherIcon name="calendar" class="h-7 w-7 text-gray-500 mr-2.5" />
        <span class="font-semibold text-2xl text-gray-500 mr-2">Roster:</span>
        <span class="font-semibold text-2xl">Month View</span>
        <div class="ml-auto space-x-2.5">
          <Dropdown
            :options="VIEW_OPTIONS"
            :button="{ label: 'View', iconRight: 'chevron-down', size: 'md' }"
          />
          <Dropdown
            :options="[
              {
                label: 'Shift Assignment',
                onClick: () => { showShiftAssignmentDialog = true },
              },
            ]"
            :button="{ label: 'Create', variant: 'solid', iconRight: 'chevron-down', size: 'md' }"
          />
        </div>
      </div>
    </div>

    <!-- Filters header -->
    <div ref="filtersRef" class="px-12 pb-4">
      <MonthViewHeader
        :firstOfMonth="firstOfMonth"
        @updateFilters="updateFilters"
        @addToMonth="addToMonth"
        @updateDateRange="onUpdateDateRange"
        @updateProjectShiftsFilled="onUpdateProjectShiftsFilled"
      />
    </div>

    <!-- Projects timeline (collapsible) -->
    <div ref="timelineRef" class="px-12 pb-4">
      <ProjectTimelineRow
        v-model:collapsed="projectsCollapsed"
        :firstOfMonth="firstOfMonth"
        :projectFilters="projectFilters"
        :dayColWidthPx="144"
        :leftColWidthPx="256"
        :scrollLeft="hScroll"
        @height="timelineHeight = $event"
      />
    </div>

    <!-- Table area fills remaining height -->
    <div class="px-12 pb-8 flex-1 min-h-0 mt-px">
      <MonthViewTable
        v-if="isCompanySelected"
        ref="monthViewTable"
        :firstOfMonth="firstOfMonth"
        :employees="availableEmployees"
        :employeeFilters="employeeFilters"
        :shiftFilters="shiftFilters"
        :maxHeightPx="tableHeight"
        @hscroll="hScroll = $event"
      />
      <div v-else class="py-40 text-center">Please select a company.</div>
    </div>
  </div>

  <ShiftAssignmentDialog
    v-model="showShiftAssignmentDialog"
    :isDialogOpen="showShiftAssignmentDialog"
    :employees="employees.data"
    @fetchEvents="
      monthViewTable?.events.fetch();
      showShiftAssignmentDialog = false;
    "
  />
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onBeforeUnmount, toRaw, watch } from 'vue'
import { Dropdown, FeatherIcon, createListResource, createResource } from 'frappe-ui'
import { dayjs, goTo, raiseToast } from '../utils'
import MonthViewTable from '../components/MonthViewTable.vue'
import ProjectTimelineRow from '../components/ProjectTimelineRow.vue'
import MonthViewHeader from '../components/MonthViewHeader.vue'
import ShiftAssignmentDialog from '../components/ShiftAssignmentDialog.vue'

export type EmployeeFilters = {
  [K in 'status' | 'company' | 'department' | 'branch' | 'designation']?: string;
};
export type ShiftFilters = {
  [K in 'shift_type' | 'shift_location']?: string;
};

type AvailabilityResponse = { employees: { name: string }[] }

const monthViewTable = ref<InstanceType<typeof MonthViewTable>>()
const isCompanySelected = ref(false)
const showShiftAssignmentDialog = ref(false)
const firstOfMonth = ref(dayjs().date(1).startOf('D'))
const employeeFilters = reactive<EmployeeFilters>({ status: 'Active' })
const shiftFilters = reactive<ShiftFilters>({})
const dateRange = reactive<{ from: string | null; to: string | null }>({ from: null, to: null })
const hScroll = ref(0)
const projectsCollapsed = ref(false)
const toolbarRef = ref<HTMLElement | null>(null)
const filtersRef = ref<HTMLElement | null>(null)
const timelineRef = ref<HTMLElement | null>(null)
const toolbarHeight = ref(0)
const filtersHeight = ref(0)
const timelineHeight = ref(0)
const vh = ref(window.innerHeight)
const projectFilters = reactive<{ company?: string; shifts_filled?: 0 | 1 }>({})
let roToolbar: ResizeObserver | null = null
let roFilters: ResizeObserver | null = null
let roTimeline: ResizeObserver | null = null

const VIEW_OPTIONS = [
  'Shift Type',
  'Shift Location',
  'Shift Assignment',
  'Shift Schedule',
  'Shift Schedule Assignment',
].map((label) => ({
  label,
  onClick: () => goTo(`/app/${label.toLowerCase().split(' ').join('-')}`),
}))

function addToMonth(change: number) {
  firstOfMonth.value = firstOfMonth.value.add(change, 'M')
  // If you want the dateRange to snap with month navigation, uncomment:
  // dateRange.from = firstOfMonth.value.startOf('month').format('YYYY-MM-DD')
  // dateRange.to   = firstOfMonth.value.endOf('month').format('YYYY-MM-DD')
  // fetchAvailability()
}

function updateFilters(newFilters: EmployeeFilters & ShiftFilters) {
  isCompanySelected.value = !!newFilters.company
  if (!isCompanySelected.value) return

  let employeeUpdated = false
  ;(Object.entries(newFilters) as [keyof EmployeeFilters | keyof ShiftFilters, string][])
    .forEach(([key, value]) => {
      if (['shift_type', 'shift_location'].includes(key as string)) {
        if (value) shiftFilters[key as keyof ShiftFilters] = value
        else delete shiftFilters[key as keyof ShiftFilters]
        return
      }
      if (value) employeeFilters[key as keyof EmployeeFilters] = value
      else delete employeeFilters[key as keyof EmployeeFilters]
      employeeUpdated = true
    })

  if (employeeUpdated) employees.fetch()
  fetchAvailability()
}

// calculate remaining height for the table scroller
const tableHeight = computed(() => {
  const innerBottomPadding = 32
  const extraShave = 50
  const used = toolbarHeight.value + filtersHeight.value + timelineHeight.value
  const remaining = vh.value - used - innerBottomPadding - extraShave
  return Math.max(200, remaining)
})

function observeHeights() {
  if (toolbarRef.value) {
    roToolbar = new ResizeObserver(() => {
      toolbarHeight.value = toolbarRef.value!.getBoundingClientRect().height
    })
    roToolbar.observe(toolbarRef.value)
  }
  if (filtersRef.value) {
    roFilters = new ResizeObserver(() => {
      filtersHeight.value = filtersRef.value!.getBoundingClientRect().height
    })
    roFilters.observe(filtersRef.value)
  }
  if (timelineRef.value) {
    roTimeline = new ResizeObserver(() => {
      timelineHeight.value = timelineRef.value!.getBoundingClientRect().height
    })
    roTimeline.observe(timelineRef.value)
  }
}

function unobserveHeights() {
  roToolbar?.disconnect()
  roFilters?.disconnect()
  roTimeline?.disconnect()
}

function onWindowResize() {
  vh.value = window.innerHeight
}

onMounted(() => {
  observeHeights()
  window.addEventListener('resize', onWindowResize)
  // initialize once
  toolbarHeight.value = toolbarRef.value?.getBoundingClientRect().height ?? 0
  filtersHeight.value = filtersRef.value?.getBoundingClientRect().height ?? 0
  timelineHeight.value = timelineRef.value?.getBoundingClientRect().height ?? 0
})

onBeforeUnmount(() => {
  unobserveHeights()
  window.removeEventListener('resize', onWindowResize)
})

const employees = createListResource({
  doctype: 'Employee',
  fields: ['name', 'employee_name', 'designation', 'image'],
  filters: employeeFilters,
  pageLength: 99999,
  onSuccess() {
    fetchAvailability()
  },
  onError(error: { messages: string[] }) {
    raiseToast('error', error.messages[0])
  },
})

const availableNameSet = ref<Set<string>>(new Set())
const availableEmployees = computed(() => {
  const base = employees.data || []
  if (!availableNameSet.value.size) return base
  return base.filter((e: any) => availableNameSet.value.has(e.name))
})

function cleaned<T extends Record<string, any>>(obj: T): Partial<T> {
  const raw = { ...toRaw(obj) }
  Object.keys(raw).forEach((k) => {
    if (raw[k] === '' || raw[k] == null) delete raw[k]
  })
  return raw
}

const availability = createResource({
  url: 'hrms.api.roster.get_available_employees',
  auto: false,
  makeParams() {
    return {
      from_date: dateRange.from,
      to_date: dateRange.to,
      ...cleaned(employeeFilters), // company/department/branch/designation
    }
  },
  onSuccess: (data: AvailabilityResponse | undefined) => {
    const names = (data?.employees || []).map((e: { name: string }) => e.name)
    availableNameSet.value = new Set(names)
  },
  onError(error: { messages?: string[]; message?: string }) {
    raiseToast('error', error?.messages?.[0] || error?.message || 'Failed to fetch availability')
    availableNameSet.value = new Set()
  },
})

function fetchAvailability() {
  if (!isCompanySelected.value || !dateRange.from || !dateRange.to) {
    availableNameSet.value = new Set() // show base list
    return
  }
  availability.fetch()
}

function onUpdateDateRange(payload: { from: string | null; to: string | null } | string) {
  if (typeof payload === 'string') {
    const [from, to] = payload.split(',').map(s => s?.trim() || '')
    dateRange.from = from || null
    dateRange.to = to || null
  } else {
    dateRange.from = payload.from
    dateRange.to = payload.to
  }
  fetchAvailability()
}

watch(
  () => employeeFilters.company,
  (company) => {
    if (company) projectFilters.company = company
    else delete projectFilters.company
  },
  { immediate: true }
)

function onUpdateProjectShiftsFilled(value: 0 | 1) {
  projectFilters.shifts_filled = value   // 0 = unfilled (default), 1 = filled
}
</script>
