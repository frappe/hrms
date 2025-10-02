<template>
  <div ref="root">
    <div
      ref="scroller"
      class="rounded-lg border overflow-auto max-h-[24rem] hide-scrollbar">
      <table class="border-separate border-spacing-0 w-full">
        <thead>
          <tr class="sticky top-0 bg-white z-10">
            <!-- Header label cell -->
            <th
              class="p-2 border-b sticky left-0 bg-white border-r cursor-pointer select-none"
              :style="leftColStyle"
              @click="toggleCollapsed"
              :aria-expanded="!internalCollapsed"
              role="button"
            >
              <div class="flex items-center gap-2">
                <FeatherIcon name="layers" class="h-4 w-4 text-gray-500" />
                <span class="font-medium">Projects</span>
                <FeatherIcon
                  name="chevron-down"
                  class="h-4 w-4 text-gray-400 transition-transform duration-200 ml-1"
                  :class="internalCollapsed ? '-rotate-90' : ''"
                  aria-hidden="true"
                />
              </div>
            </th>

            <!-- Days -->
            <th
              v-for="(day, idx) in daysOfMonth"
              :key="idx"
              class="font-medium border-b text-center"
              :class="{ 'border-l': idx }"
              :style="dayThStyle"
            >
              {{ day.dayName }} {{ dayjs(day.date).format('DD') }}
            </th>
          </tr>
        </thead>

        <tbody  v-show="!internalCollapsed">
          <tr>
            <!-- Left title cell -->
            <td
              class="border-t sticky left-0 bg-white border-r align-top z-[5]"
              :style="leftColStyle"
            >
            <!-- Show all projects toggle -->
            <div class="ml-4">
              <FormControl
                type="checkbox"
                label="Show All"
                v-model="showAllProjects"
              />
            </div>
              <!-- Legend -->
            <div class="px-2 py-1.5">
              <div class="text-xs font-medium text-gray-600 mb-1"><b>Legend</b></div>
              <div class="flex items-center gap-3 text-xs text-gray-600">
                <span class="inline-flex items-center gap-1.5">
                  <FeatherIcon name="check-circle" class="h-3.5 w-3.5 text-green-500" aria-hidden="true" />
                  PO Entered
                </span>
              </div>
              <div class="flex items-center gap-3 text-xs text-gray-600">
                <span class="inline-flex items-center gap-1.5">
                  <FeatherIcon name="x-circle" class="h-3.5 w-3.5 text-red-500" aria-hidden="true" />
                  PO Missing
                </span>
              </div>
              <div class="flex items-center gap-3 text-xs text-gray-600">
                <span class="inline-flex items-center gap-1.5">
                  <FeatherIcon name="sun" class="h-3.5 w-3.5 text-orange-500" aria-hidden="true" />
                  # DS Requested
                </span>
              </div>
              <div class="flex items-center gap-3 text-xs text-gray-600">
                <span class="inline-flex items-center gap-1.5">
                  <FeatherIcon name="moon" class="h-3.5 w-3.5 text-blue-500" aria-hidden="true" />
                  # NS Requested
                </span>
              </div>
            </div>
            </td>

            <!-- One-row grid for bars -->
            <td class="p-0 border-t" :colspan="daysOfMonth.length">
              <div
                class="relative"
                :style="{
                  display: 'grid',
                  gridTemplateColumns: `repeat(${daysOfMonth.length}, ${dayColWidth}px)`,
                  gap: '0px',
                  padding: '6px 0',
                  minHeight: bars.length ? '48px' : '36px',
                  minWidth: `${daysOfMonth.length * dayColWidth}px`,
                }"
              >
                <!-- Project bars -->
                <div
                  v-for="bar in bars"
                  :key="bar.key"
                  class="rounded border text-xs px-2 py-1 overflow-hidden whitespace-nowrap"
                  :style="{
                    gridColumn: `${bar.startCol} / ${bar.endCol + 1}`,
                    borderColor: hexToRgba(bar.color || '', 0.5),
                    backgroundColor: hexToRgba(bar.color || '', 0.12),
                  }"
                  :title="bar.tooltip"
                >
                  <div class="flex items-center gap-2">
                    <FeatherIcon
                      :name="bar.hasPO ? 'check-circle' : 'x-circle'"
                      class="h-3.5 w-3.5 flex-shrink-0"
                      :class="bar.hasPO ? 'text-green-500' : 'text-red-500'"
                      aria-hidden="true"
                    />
                    <span class="font-medium truncate">
                      {{ bar.projectLabel }}
                    </span>
                    <span class="text-gray-500">
                      {{ dayjs(bar.projectStart).format('D MMM') }} – {{ dayjs(bar.projectEnd).format('D MMM') }}
                    </span>
                    <FeatherIcon name="sun" class="h-3.5 w-3.5 flex-shrink-0 text-orange-500" aria-hidden="true" />
                    <span class="font-medium truncate">{{ bar.day_shift }}</span>
                    <FeatherIcon name="moon" class="h-3.5 w-3.5 flex-shrink-0 text-blue-500" aria-hidden="true" />
                    <span class="font-medium truncate">{{ bar.night_shift }}</span>
                  </div>
                </div>

                <!-- Empty state -->
                <div v-if="!bars.length" class="text-xs text-gray-500">
                  All Projects assigned.
                </div>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch, onMounted, onBeforeUnmount } from 'vue'
import { FeatherIcon, FormControl, Popover, createListResource } from 'frappe-ui'
import { Dayjs } from 'dayjs'
import { dayjs, raiseToast } from '../utils'

const showAllProjects = ref(false)
/**
 * Props:
 * - firstOfMonth: Dayjs for the month to render
 * - projectFilters (optional): additional filters (e.g., company)
 *     You can pass object filters like { company: 'Acme' } and they’ll be ANDed with status != Completed.
 */
const props = defineProps<{
  firstOfMonth: Dayjs
  projectFilters?: { company?: string; shifts_filled?: 0 | 1 }
  dayColWidthPx?: number
  leftColWidthPx?: number
  scrollLeft?: number
  collapsed?: boolean
}>()

const emit = defineEmits<{
  (e: 'update:collapsed', v: boolean): void
  (e: 'height', px: number): void
}>()

// Internal shifts_filled flag (0=unfilled default, 1=filled)
const shiftsFilled = ref<number>(props.projectFilters?.shifts_filled ?? 0)
// Checkbox boolean ↔ 0/1 mapper
const showFilledProjects = computed<boolean>({
  get: () => shiftsFilled.value === 1,
  set: (checked) => { shiftsFilled.value = checked ? 1 : 0 }
})
// If the parent ever sends a new value, sync it (optional)
watch(() => props.projectFilters?.shifts_filled, (v) => {
  if (v === 0 || v === 1) shiftsFilled.value = v
})

// local collapsible state (controlled or uncontrolled)
const internalCollapsed = ref(!!props.collapsed)
watch(() => props.collapsed, v => {
  if (typeof v === 'boolean') internalCollapsed.value = v
})
function toggleCollapsed() {
  internalCollapsed.value = !internalCollapsed.value
  emit('update:collapsed', internalCollapsed.value)
  // give DOM a tick, then measure
  requestAnimationFrame(reportHeight)
}

const dayColWidth = computed(() => props.dayColWidthPx ?? 144)
const leftColWidth = computed(() => props.leftColWidthPx ?? 256)
const scroller = ref<HTMLDivElement | null>(null)

const root = ref<HTMLDivElement | null>(null)
let ro: ResizeObserver | null = null

function reportHeight() {
  if (!root.value) return
  emit('height', root.value.getBoundingClientRect().height)
}

onMounted(() => {
  if (root.value && 'ResizeObserver' in window) {
    ro = new ResizeObserver(() => reportHeight())
    ro.observe(root.value)
  }
  // initial fire
  reportHeight()
})
onBeforeUnmount(() => {
  if (ro && root.value) ro.disconnect()
})

const leftColStyle = computed(() => ({
  width: `${leftColWidth.value}px`,
  minWidth: `${leftColWidth.value}px`,
  maxWidth: `${leftColWidth.value}px`,
}))

const dayThStyle = computed(() => ({
  width: `${dayColWidth.value}px`,
  minWidth: `${dayColWidth.value}px`,
  maxWidth: `${dayColWidth.value}px`,
}))

type ProjectRow = {
  name: string
  project_name: string
  status: string
  expected_start_date?: string | null
  expected_end_date?: string | null
  color?: string | null
  customer?: string | null
  custom_project_location?: string | null
  purchase_order_number?: string | null
  ds_number?: string | null
  ns_number?: string | null
  customer_abbreviation?: string | null
}

const loading = ref(true)

const daysOfMonth = computed(() => {
  const arr: { dayName: string; date: string }[] = []
  for (let i = 1; i <= props.firstOfMonth.daysInMonth(); i++) {
    const d = props.firstOfMonth.date(i)
    arr.push({ dayName: d.format('ddd'), date: d.format('YYYY-MM-DD') })
  }
  return arr
})

/**
 * Fetch Projects directly.
 * We use a NOT-EQUAL filter for status != Completed, plus any extra filters from props.projectFilters.
 * We pull more than the default 20 via page_length.
 */
const projectList = createListResource({
  doctype: 'Project',
  fields: [
    'name',
    'project_name',
    'status',
    'expected_start_date',
    'expected_end_date',
    'color',
    'customer',
    'custom_project_location',
    'purchase_order_number',
    'ds_number',
    'ns_number',
    'customer_abbreviation',
  ],
  // Use array filters to express '!=' reliably in Frappe
  filters: computed(() => {
    const base: any[] = [
      ['Project', 'status', '!=', 'Completed'],
    ]
    // Only filter by unfilled when NOT showing all
    if (!showAllProjects.value) {
      base.push(['Project', 'shifts_filled', '=', 0])
    }

    // Merge the rest of projectFilters (skip shifts_filled)
    if (props.projectFilters) {
      for (const [k, v] of Object.entries(props.projectFilters)) {
        if (k === 'shifts_filled' || v == null || v === '') continue
        base.push(['Project', k, '=', v])
      }
    }
    return base
  }),
  order_by: 'expected_start_date asc',
  page_length: 1000,
  auto: false,
  onSuccess() {
    loading.value = false
  },
  onError(error: { messages: string[] }) {
    loading.value = false
    raiseToast('error', error.messages[0])
  },
})

// Refetch when the toggle changes
watch(showAllProjects, () => {
  loading.value = true
  projectList.fetch()
})

watch(
  () => props.scrollLeft,
  (x) => {
    if (typeof x === 'number' && scroller.value && scroller.value.scrollLeft !== x) {
      scroller.value.scrollLeft = x
    }
  }
)

// Fetch when month or external filters change
watch(
  () => [props.firstOfMonth, props.projectFilters],
  () => {
    loading.value = true
    projectList.fetch()
  },
  { deep: true, immediate: true } // immediate to load on mount
)

/** Helper: get start/end with fallbacks and clamp to month window */
function clampToMonth(row: ProjectRow): { start: string | null; end: string | null } {
  const mStart = props.firstOfMonth.startOf('month')
  const mEnd   = props.firstOfMonth.endOf('month')

  // prefer expected_*; fallback to start_date/end_date
  const rawStart = row.expected_start_date ?? null
  const rawEnd   = row.expected_end_date ?? null

  if (!rawStart && !rawEnd) return { start: null, end: null }

  const s = rawStart ? dayjs(rawStart) : (rawEnd ? dayjs(rawEnd) : null)
  if (!s) return { start: null, end: null }

  const e = rawEnd ? dayjs(rawEnd) : s // if no end, treat as same day

  // Skip if completely outside month
  const overlaps = s.isSameOrBefore(mEnd) && e.isSameOrAfter(mStart)
  if (!overlaps) return { start: null, end: null }

  const cs = s.isBefore(mStart) ? mStart : s
  const ce = e.isAfter(mEnd) ? mEnd : e

  return { start: cs.format('YYYY-MM-DD'), end: ce.format('YYYY-MM-DD') }
}

function hexToRgba(hex: string, alpha: number) {
  if (!hex) return `rgba(59,130,246,${alpha})` // fallback (Tailwind blue-500)
  let h = hex.trim()
  if (h.startsWith('#')) h = h.slice(1)
  if (h.length === 3) {
    // e.g. #0af -> #00aaff
    h = h.split('').map(ch => ch + ch).join('')
  }
  const int = parseInt(h, 16)
  if (Number.isNaN(int) || h.length !== 6) return `rgba(59,130,246,${alpha})`
  const r = (int >> 16) & 255
  const g = (int >> 8) & 255
  const b = int & 255
  return `rgba(${r}, ${g}, ${b}, ${alpha})`
}

/** Build bar geometry for grid-span rendering */
const bars = computed(() => {
  const rows = (projectList.data as ProjectRow[]) || []
  const days = daysOfMonth.value
  const idxOf = (isoDate: string) => {
    const i = days.findIndex(d => d.date === isoDate)
    return i >= 0 ? i + 1 : 1 // CSS grid columns are 1-based
  }

  const out: {
    key: string
    projectLabel: string
    projectStart: string
    projectEnd: string
    start: string
    end: string
    startCol: number
    endCol: number
    tooltip: string
    color: string | null
    poNumber?: string | null
    hasPO: boolean
    shiftLabel: string
    day_shift: string
    night_shift: string
    customer_abbr: string
  }[] = []

  for (const r of rows) {
    const clamped = clampToMonth(r)
    if (!clamped.start || !clamped.end) continue
    const customer = r.customer ?? "Pending"
    const customer_abbr = r.customer_abbreviation ?? "N/A"
    const location = r.custom_project_location ?? "Not Specified"
    const day_shift = r.ds_number ?? "Not Specified"
    const night_shift = r.ns_number ?? "Not Specified"
    const projectLabel = `${r.project_name} - ${customer_abbr}`
    const startCol = idxOf(clamped.start)
    const endCol   = idxOf(clamped.end)
    const poNumber = r.purchase_order_number ? ` | PO: ${r.purchase_order_number}` : ' | PO: Pending'
    const hasPO = !!r.purchase_order_number
    const shiftLabel = `DS: ${day_shift} | NS: ${night_shift}`

    out.push({
      key: `${r.name}:${clamped.start}-${clamped.end}`,
      projectLabel,
      projectStart: r.expected_start_date ?? 'N/A',
      projectEnd: r.expected_end_date ?? 'N/A',
      start: clamped.start,
      end: clamped.end,
      startCol,
      endCol,
      tooltip: [
        `Customer: ${customer}`,
        `Location: ${location}`,
        `Duration: ${dayjs(clamped.start).format('D MMM')} – ${dayjs(clamped.end).format('D MMM')}`,
        `Shifts Req: ${shiftLabel}`,
        [poNumber].filter(Boolean).join(' ')
      ].filter(Boolean).join('\n'),
      color: r.color ?? null,
      poNumber,
      hasPO,
      shiftLabel,
      day_shift,
      night_shift,
      customer_abbr,
    })
  }

  // Sort by start column for nicer layout
  out.sort((a, b) => a.startCol - b.startCol || a.endCol - b.endCol)
  return out
})
</script>

<style scoped>
th, td {
  font-size: 0.875rem;
}
/* Global scrollbar hiding for the timeline scroller */
.hide-scrollbar {
  /* Firefox */
  scrollbar-width: none;
  /* IE/old Edge */
  -ms-overflow-style: none;
}

.hide-scrollbar::-webkit-scrollbar {
  /* Chrome/Safari/Edge (Blink/WebKit) */
  width: 0;
  height: 0;
  display: none;
}
</style>
