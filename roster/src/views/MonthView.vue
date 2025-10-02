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
      />
    </div>

    <!-- Projects timeline (collapsible) -->
    <div ref="timelineRef" class="px-12 pb-4">
      <ProjectTimelineRow
        v-model:collapsed="projectsCollapsed"
        :firstOfMonth="firstOfMonth"
        :projectFilters="{ company: employeeFilters.company }"
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
        :employees="employees.data || []"
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
import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue'
import { Dropdown, FeatherIcon, createListResource } from 'frappe-ui'

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

const monthViewTable = ref<InstanceType<typeof MonthViewTable>>()
const isCompanySelected = ref(false)
const showShiftAssignmentDialog = ref(false)
const firstOfMonth = ref(dayjs().date(1).startOf('D'))
const employeeFilters = reactive<EmployeeFilters>({ status: 'Active' })
const shiftFilters = reactive<ShiftFilters>({})

// horizontal scroll sync
const hScroll = ref(0)
// projects section collapsed state (two-way bound with ProjectTimelineRow)
const projectsCollapsed = ref(false)

// dynamic height measurement
const toolbarRef = ref<HTMLElement | null>(null)
const filtersRef = ref<HTMLElement | null>(null)
const timelineRef = ref<HTMLElement | null>(null)
const toolbarHeight = ref(0)
const filtersHeight = ref(0)
const timelineHeight = ref(0)
const vh = ref(window.innerHeight)

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
}

// calculate remaining height for the table scroller
const tableHeight = computed(() => {
  const innerBottomPadding = 32 /* pb-8 */
  const extraShave = 50       /* reduce overall height by 50px */
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

// RESOURCES
const employees = createListResource({
  doctype: 'Employee',
  fields: ['name', 'employee_name', 'designation', 'image'],
  filters: employeeFilters,
  pageLength: 99999,
  onError(error: { messages: string[] }) {
    raiseToast('error', error.messages[0])
  },
})
</script>
