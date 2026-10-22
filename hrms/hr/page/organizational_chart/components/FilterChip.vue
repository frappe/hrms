<script setup lang="ts">
// A toggle with a count: "On leave 2". The count is the point, so it never hides.
import { Button } from 'frappe-ui'
defineProps<{ label: string; icon?: string; count?: number; active?: boolean }>()
</script>

<template>
  <Button :variant="active ? 'subtle' : 'outline'" :icon-left="icon" :aria-pressed="active">
    {{ label }} <span class="ml-1 tabular-nums text-ink-gray-5">{{ count }}</span>
  </Button>
</template>
