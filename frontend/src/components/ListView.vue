<template>
	<div class="flex flex-col h-screen w-screen">
		<div class="w-full sm:w-96">
			<header
				class="flex flex-row bg-white shadow-sm py-4 px-2 items-center justify-between border-b sticky top-0 z-10"
			>
				<div class="flex flex-row gap-1">
					<Button
						appearance="minimal"
						class="!px-0 !py-0"
						@click="router.back()"
					>
						<FeatherIcon name="chevron-left" class="h-5 w-5" />
					</Button>
					<h2 class="text-2xl font-semibold text-gray-900">{{ pageTitle }}</h2>
				</div>

				<div class="flex flex-row gap-2">
					<Button
						id="open-filter-view"
						icon="filter"
						appearance="secondary"
						:class="[
							areFiltersApplied
								? '!border border-blue-500 bg-white !text-blue-500'
								: '',
						]"
					/>
					<router-link :to="{ name: formViewRoute }" v-slot="{ navigate }">
						<Button
							icon-left="plus"
							appearance="primary"
							class="mr-2"
							@click="navigate"
						>
							New
						</Button>
					</router-link>
				</div>
			</header>

			<div class="flex flex-col items-center mt-5 mb-7 p-4">
				<div class="w-full">
					<TabButtons
						:buttons="[{ label: tabButtons[0] }, { label: tabButtons[1] }]"
						v-model="activeTab"
					/>

					<div
						class="flex flex-col bg-white rounded-lg mt-5 overflow-auto"
						v-if="documents.data?.length"
					>
						<div
							class="p-3.5 items-center justify-between border-b cursor-pointer"
							v-for="link in documents.data"
							:key="link.name"
						>
							<router-link
								:to="{ name: detailViewRoute, params: { id: link.name } }"
								v-slot="{ navigate }"
							>
								<component
									:is="listItemComponent[doctype]"
									:doc="link"
									:isTeamRequest="isTeamRequest"
									@click="navigate"
								/>
							</router-link>
						</div>
					</div>
					<EmptyState message="No leaves found" v-else />
				</div>
			</div>

			<!-- Loading Indicator -->
			<div
				v-if="documents.loading"
				class="flex h-64 items-center justify-center"
			>
				<LoadingIndicator class="w-8 h-8 text-blue-500" />
			</div>

			<!-- Filter Action Sheet -->
			<ion-modal
				ref="modal"
				trigger="open-filter-view"
				:initial-breakpoint="1"
				:breakpoints="[0, 1]"
			>
				<div
					class="bg-white w-full flex flex-col items-center justify-center pb-5"
				>
					<div class="w-full pt-8 pb-5 border-b text-center">
						<span class="text-gray-900 font-bold text-xl">Filters</span>
					</div>
					<div
						class="w-full flex flex-col items-center justify-center gap-5 p-4"
					>
						<!-- Status filter -->
						<div class="flex flex-col w-full">
							<div class="text-gray-800 font-bold text-lg">Status</div>
							<div class="flex flex-row gap-2 mt-2">
								<Button
									v-for="option in statusFilterOptions"
									@click="filterByStatus = option"
									appearance="white"
									:class="[
										option === filterByStatus
											? 'border border-blue-500 !text-blue-500'
											: '',
									]"
								>
									{{ option }}
								</Button>
							</div>
						</div>

						<!-- Filter Buttons -->
						<div
							class="flex w-full flex-row items-center justify-between gap-3"
						>
							<Button
								@click="clearFilters"
								appearance="secondary"
								class="w-full py-3 px-12"
							>
								Clear All
							</Button>
							<Button
								@click="applyFilters"
								appearance="primary"
								class="w-full py-3 px-12"
							>
								Apply Filters
							</Button>
						</div>
					</div>
				</div>
			</ion-modal>
		</div>
	</div>
</template>

<script setup>
import { useRouter } from "vue-router"
import { inject, ref, markRaw, watch, computed } from "vue"
import { IonModal, modalController } from "@ionic/vue"

import { FeatherIcon, createResource, LoadingIndicator } from "frappe-ui"

import TabButtons from "@/components/TabButtons.vue"
import LeaveRequestItem from "@/components/LeaveRequestItem.vue"

const props = defineProps({
	doctype: {
		type: String,
		required: true,
	},
	fields: {
		type: Array,
		required: true,
	},
	tabButtons: {
		type: Array,
		required: true,
	},
	pageTitle: {
		type: String,
		required: false,
	},
	statusFilterOptions: {
		type: Array,
		required: false,
	},
})

const listItemComponent = {
	"Leave Application": markRaw(LeaveRequestItem),
}

const router = useRouter()
const employee = inject("$employee")
const activeTab = ref(props.tabButtons[0])
const filterByStatus = ref(null)
const areFiltersApplied = ref(false)

const isTeamRequest = computed(() => {
	return activeTab.value === props.tabButtons[1]
})

const formViewRoute = computed(() => {
	return `${props.doctype.replace(/\s+/g, "")}FormView`
})

const detailViewRoute = computed(() => {
	return `${props.doctype.replace(/\s+/g, "")}DetailView`
})

const appliedFilters = computed(() => {
	const filters = []

	if (isTeamRequest.value) {
		filters.push([props.doctype, "employee", "!=", employee.data.name])
	} else {
		filters.push([props.doctype, "employee", "=", employee.data.name])
	}

	if (filterByStatus.value) {
		filters.push([props.doctype, "status", "=", filterByStatus.value])
	}

	return filters
})

function applyFilters() {
	fetchDocumentList()
	modalController.dismiss()
	areFiltersApplied.value = true
}

function clearFilters() {
	filterByStatus.value = []
	fetchDocumentList()
	modalController.dismiss()
	areFiltersApplied.value = false
}

function fetchDocumentList() {
	const filters = [[props.doctype, "docstatus", "!=", "2"]]
	filters.push(...appliedFilters.value)

	documents.submit({
		doctype: props.doctype,
		fields: props.fields,
		filters: filters,
	})
}

const documents = createResource({
	url: "frappe.desk.reportview.get",
	transform(data) {
		if (data.length === 0) {
			return []
		}

		// convert keys and values arrays to docs object
		const fields = data["keys"]
		const values = data["values"]
		const docs = values.map((value) => {
			const doc = {}
			fields.forEach((field, index) => {
				doc[field] = value[index]
			})
			return doc
		})
		return docs
	},
})

watch(
	() => activeTab.value,
	(_value) => {
		fetchDocumentList()
	},
	{ immediate: true }
)
</script>
