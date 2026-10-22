<script setup lang="ts">
// The search box with its icon.
import { TextInput } from 'frappe-ui'
declare const __: (text: string) => string
defineProps<{ modelValue?: string; placeholder?: string }>()
const emit = defineEmits<{ 'update:modelValue': [value: string] }>()
</script>

<template>
  <TextInput
    class="w-full"
    type="search"
    :model-value="modelValue"
    :placeholder="placeholder"
    :aria-label="__('Search people')"
    @update:model-value="(v: string) => emit('update:modelValue', v ?? '')"
  >
    <template #prefix><span class="lucide-search size-4 text-ink-gray-5" aria-hidden="true" /></template>
  </TextInput>
</template>
