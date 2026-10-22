<script setup lang="ts">
// The one empty state. `compact` for inside a section, default for a whole page.
defineProps<{ icon?: string; title: string; description?: string; compact?: boolean }>()
</script>

<template>
  <div
    class="flex flex-col items-center justify-center text-center"
    :class="compact ? 'gap-2 rounded-5 border border-dashed border-outline-gray-2 px-4 py-8' : 'gap-3 py-20'"
  >
    <div v-if="icon" class="flex size-10 items-center justify-center rounded-full bg-surface-gray-2 text-ink-gray-5">
      <span :class="[icon, 'size-5']" aria-hidden="true" />
    </div>
    <p class="text-base-medium text-ink-gray-8">{{ title }}</p>
    <p v-if="description" class="max-w-sm text-p-base text-ink-gray-5">{{ description }}</p>
    <div v-if="$slots.default" class="mt-1 flex items-center gap-2"><slot /></div>
  </div>
</template>
