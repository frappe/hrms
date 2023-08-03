<template>
	<!-- Filter Action Sheet -->
	<div class="bg-white w-full flex flex-col items-center justify-center pb-5">
		<div class="w-full pt-8 pb-5 border-b text-center">
			<span class="text-gray-900 font-bold text-xl">Filters</span>
		</div>
		<div class="w-full flex flex-col items-center justify-center gap-5 p-4">
			<div
				v-for="filter in filterConfig"
				:key="filter.fieldname"
				class="flex flex-col w-full gap-1"
			>
				<!-- Status filter -->
				<div
					class="flex flex-col"
					v-if="['status', 'approval_status'].includes(filter.fieldname)"
				>
					<div class="text-gray-800 font-semibold text-lg">
						{{ filter.label }}
					</div>
					<div class="flex flex-row gap-2 mt-2">
						<Button
							v-for="option in filter.options"
							appearance="white"
							@click="filters[filter.fieldname].value = option"
							:class="[
								option === filters[filter.fieldname].value
									? '!border !border-blue-500 !text-blue-500'
									: '',
							]"
						>
							{{ option }}
						</Button>
					</div>
				</div>

				<!-- Field filters -->
				<div v-else class="flex flex-col gap-2">
					<div class="text-gray-800 font-semibold text-lg">
						{{ filter.label }}
					</div>
					<div class="flex flex-row items-center gap-2 w-full">
						<ion-list
							class="h-[26px] w-full rounded-md p-0 mt-1"
							v-if="filterConditionMap[filter.fieldtype]"
						>
							<ion-item class="rounded-md text-center justify-center">
								<ion-select
									class="-top-3.5 m-0 appearance-none rounded-md text-base"
									interface="action-sheet"
									aria-label="fruit"
									toggle-icon=""
									placeholder="Select Operator"
									v-model="filters[filter.fieldname].condition"
								>
									<ion-select-option
										v-for="condition in filterConditionMap[filter.fieldtype]"
										:value="condition"
										:key="condition"
										:selected="condition === '='"
									>
										{{ condition }}
									</ion-select-option>
								</ion-select>
							</ion-item>
						</ion-list>
						<FormField
							class="w-full"
							:fieldtype="filter.fieldtype"
							:fieldname="filter.fieldname"
							:options="filter.options"
							v-model="filters[filter.fieldname].value"
						/>
					</div>
				</div>
			</div>

			<!-- Filter Buttons -->
			<div class="flex w-full flex-row items-center justify-between gap-3">
				<Button
					@click="emit('clear-filters')"
					appearance="secondary"
					class="w-full py-3 px-12"
				>
					Clear All
				</Button>
				<Button
					@click="emit('apply-filters')"
					appearance="primary"
					class="w-full py-3 px-12"
				>
					Apply Filters
				</Button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue"
import { IonList, IonItem, IonSelect, IonSelectOption } from "@ionic/vue"
import FormField from "@/components/FormField.vue"

const props = defineProps({
	filterConfig: {
		type: Array,
		required: true,
	},
	filters: {
		type: Object,
		required: true,
	},
})

const emit = defineEmits(["apply-filters", "clear-filters", "update:filters"])

const filterConditionMap = {
	Date: ["=", ">", "<", ">=", "<="],
}

const filters = computed({
	get() {
		return props.filters
	},
	set(value) {
		emit("update:filters", value)
	},
})
</script>
