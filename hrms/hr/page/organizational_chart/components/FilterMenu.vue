<script setup lang="ts">
// A button that opens a list and remembers the pick: Department, Office. The button shows the
// pick, or the label when nothing is picked ("All" is the empty value).
import { computed } from 'vue'
import { Button, Dropdown } from 'frappe-ui'

const props = withDefaults(defineProps<{ modelValue?: string; label: string; icon?: string; options?: string[]; allLabel: string }>(), { options: () => [] })
const emit = defineEmits<{ 'update:modelValue': [value: string] }>()

const items = computed(() => [
  { label: props.allLabel, selected: !props.modelValue, onClick: () => emit('update:modelValue', '') },
  ...props.options.map((o) => ({ label: o, selected: props.modelValue === o, onClick: () => emit('update:modelValue', o) })),
])
</script>

<template>
  <Dropdown :options="items" align="end">
    <Button variant="subtle" :icon-left="icon" icon-right="lucide-chevron-down" :label="modelValue || label" />
  </Dropdown>
</template>
