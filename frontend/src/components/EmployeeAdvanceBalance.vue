<template>
	<div
		class="flex flex-col bg-white rounded-lg mt-5 overflow-auto"
		v-if="props.items?.length"
	>
		<div
			class="flex flex-row p-3.5 items-center justify-between border-b cursor-pointer"
			v-for="link in props.items"
			:key="link.name"
			@click="openRequestModal(link)"
		>
			<EmployeeAdvanceItem :doc="link" />
		</div>

		<router-link
			:to="{ name: 'EmployeeAdvanceFormView' }"
			v-slot="{ navigate }"
		>
			<div class="flex flex-col bg-white w-full py-5 px-3.5 mt-0 border-none">
				<Button @click="navigate" appearance="secondary" class="py-2">
					Request an Advance
				</Button>
			</div>
		</router-link>
	</div>
	<EmptyState message="You have no advances" v-else />
</template>

<script setup>
import EmployeeAdvanceItem from "@/components/EmployeeAdvanceItem.vue"

const props = defineProps({
	items: {
		type: Array,
	},
})
</script>
