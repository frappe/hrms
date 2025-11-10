<template>
	<div
		class="flex flex-col bg-white rounded mt-5 overflow-auto"
		v-if="props.items?.length"
	>
		<router-link
			v-for="link in props.items"
			:key="link.name"
			:to="{ name: 'EmployeeAdvanceDetailView', params: { id: link.name } }"
			class="flex flex-row p-3.5 items-center justify-between border-b cursor-pointer"
		>
			<EmployeeAdvanceItem :doc="link" />
		</router-link>

		<router-link
			:to="{ name: 'EmployeeAdvanceFormView' }"
			v-slot="{ navigate }"
		>
			<div class="flex flex-col bg-white w-full py-5 px-3.5 mt-0 border-none">
				<Button @click="navigate" variant="subtle" class="py-5 text-base">
					{{ __("Request an Advance") }}
				</Button>
			</div>
		</router-link>
	</div>
	<EmptyState :message="__('You have no advances')" v-else />
</template>

<script setup>
import EmployeeAdvanceItem from "@/components/EmployeeAdvanceItem.vue"
import { inject } from "vue"

const __ = inject("$translate")
const props = defineProps({
	items: {
		type: Array,
	},
})
</script>
