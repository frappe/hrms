<script setup lang="ts">
// The compact card that floats beside a person on the org chart: who they are, where they
// sit, and the things you'd do next. Small enough to keep the tree readable.
import { computed } from 'vue'
import { Avatar, Button, Tooltip } from 'frappe-ui'
import MomentBadge from './MomentBadge.vue'
import { byId, deptOf, meId, reportsOf } from '../lib/people'
import { openEmployee } from '../lib/nav'

declare const __: (text: string, args?: unknown[]) => string

const props = defineProps<{ id: string }>()
const emit = defineEmits<{ close: []; team: [id: string] }>()

const p = computed(() => byId.value[props.id])
const team = computed(() => reportsOf(props.id))
const manager = computed(() => (p.value?.manager ? byId.value[p.value.manager] : null))
</script>

<template>
  <div v-if="p" class="w-full rounded-6 border border-outline-gray-2 bg-surface-base p-4 shadow-lg">
    <div class="flex items-start gap-3">
      <Avatar :image="p.photo" :label="p.name" size="2xl" class="shrink-0" />
      <div class="min-w-0 flex-1">
        <div class="flex items-center gap-2">
          <span class="truncate text-base-semibold text-ink-gray-9">{{ p.name }}</span>
          <span v-if="p.id === meId" class="shrink-0 text-sm text-ink-gray-5">{{ __('You') }}</span>
        </div>
        <div class="mt-0.5 truncate text-sm text-ink-gray-6">{{ p.role }}</div>
      </div>
      <Button class="-mr-1.5 -mt-1.5" variant="ghost" icon="lucide-x" :aria-label="__('Close')" @click="emit('close')" />
    </div>

    <MomentBadge :id="p.id" class="mt-3" />

    <dl class="mt-3 space-y-1.5 text-base">
      <div class="flex items-center gap-2">
        <dt class="lucide-building-2 size-4 shrink-0 text-ink-gray-5" :aria-label="__('Department')" />
        <dd class="min-w-0 truncate text-ink-gray-7">{{ deptOf(p.id) }}</dd>
      </div>
      <div v-if="p.office" class="flex items-center gap-2">
        <dt class="lucide-map-pin size-4 shrink-0 text-ink-gray-5" :aria-label="__('Office')" />
        <dd class="min-w-0 truncate text-ink-gray-7">{{ p.office }}</dd>
      </div>
      <div v-if="team.length" class="flex items-center gap-2">
        <dt class="lucide-users size-4 shrink-0 text-ink-gray-5" :aria-label="__('Reports')" />
        <dd class="min-w-0 truncate text-ink-gray-7">{{ team.length === 1 ? __('1 report') : __('{0} reports', [team.length]) }}</dd>
      </div>
      <div v-if="manager" class="flex items-center gap-2">
        <dt class="lucide-arrow-up-right size-4 shrink-0 text-ink-gray-5" :aria-label="__('Reports to')" />
        <dd class="flex min-w-0 items-center gap-2 text-ink-gray-7">
          <Avatar :image="manager.photo" :label="manager.name" size="xs" class="shrink-0" />
          <span class="truncate">{{ manager.name }}</span>
        </dd>
      </div>
    </dl>

    <div class="mt-4 flex items-center gap-2">
      <Button class="flex-1" variant="subtle" :label="__('Open profile')" @click="openEmployee(p.id)" />
      <Tooltip v-if="p.email" :text="p.email">
        <Button variant="subtle" icon="lucide-mail" :aria-label="__('Email {0}', [p.name])" :href="`mailto:${p.email}`" />
      </Tooltip>
      <Tooltip v-if="team.length" :text="__('Show team')">
        <Button variant="subtle" icon="lucide-git-fork" :aria-label="__('Show team')" @click="emit('team', p.id)" />
      </Tooltip>
    </div>
  </div>
</template>
