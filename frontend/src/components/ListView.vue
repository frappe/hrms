<template>
	<ion-page>
		<ion-header class="ion-no-border">
			<div class="w-full sm:w-96">
				<div
					class="flex flex-row bg-white shadow-sm py-4 px-3 items-center justify-between border-b"
				>
					<div class="flex flex-row items-center">
						<Button
							variant="ghost"
							class="!pl-0 hover:bg-white"
							@click="router.back()"
						>
							<FeatherIcon name="chevron-left" class="h-5 w-5" />
						</Button>
						<h2 class="text-xl font-semibold text-gray-900">{{ pageTitle }}</h2>
					</div>

					<div class="flex flex-row gap-2">
						<Button
							id="show-filter-modal"
							icon="filter"
							variant="subtle"
							:class="[
								areFiltersApplied
									? '!border !border-gray-800 !bg-white !text-gray-900 !font-semibold'
									: '',
							]"
						/>
						<router-link :to="{ name: formViewRoute }" v-slot="{ navigate }">
							<Button variant="solid" class="mr-2" @click="navigate">
								<template #prefix>
									<FeatherIcon name="plus" class="w-4" />
								</template>
								New
							</Button>
						</router-link>
					</div>
				</div>
			</div>
		</ion-header>

		<ion-content>
			<ion-refresher slot="fixed" @ionRefresh="handleRefresh($event)">
				<ion-refresher-content></ion-refresher-content>
			</ion-refresher>

			<div
				class="flex flex-col items-center mb-7 p-4 h-full w-full sm:w-96 overflow-y-auto"
				ref="scrollContainer"
				@scroll="() => handleScroll()"
			>
				<div class="w-full mt-5">
					<TabButtons
						:buttons="[{ label: tabButtons[0] }, { label: tabButtons[1] }]"
						v-model="activeTab"
					/>

					<div
						class="flex flex-col bg-white rounded mt-5"
						v-if="!documents.loading && documents.data?.length"
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
									:workflowStateField="workflowStateField"
									@click="navigate"
								/>
							</router-link>
						</div>
					</div>
					<EmptyState
						:message="`No ${props.doctype?.toLowerCase()}s found`"
						v-else-if="!documents.loading"
					/>

					<!-- Loading Indicator -->
					<div
						v-if="documents.loading"
						class="flex mt-2 items-center justify-center"
					>
						<LoadingIndicator class="w-8 h-8 text-gray-800" />
					</div>
				</div>
			</div>

			<CustomIonModal trigger="show-filter-modal">
				<!-- Filter Action Sheet -->
				<template #actionSheet>
					<ListFiltersActionSheet
						:filterConfig="filterConfig"
						@applyFilters="applyFilters"
						@clearFilters="clearFilters"
						v-model:filters="filterMap"
					/>
				</template>
			</CustomIonModal>
		</ion-content>
	</ion-page>
</template>

<script setup>
import { useRouter } from "vue-router"
import {
	inject,
	ref,
	markRaw,
	watch,
	computed,
	reactive,
	onMounted,
	onBeforeUnmount,
} from "vue"
import {
	modalController,
	IonPage,
	IonHeader,
	IonContent,
	IonRefresher,
	IonRefresherContent,
} from "@ionic/vue"

import {
	FeatherIcon,
	createResource,
	LoadingIndicator,
	debounce,
} from "frappe-ui"

import TabButtons from "@/components/TabButtons.vue"
import LeaveRequestItem from "@/components/LeaveRequestItem.vue"
import ExpenseClaimItem from "@/components/ExpenseClaimItem.vue"
import EmployeeAdvanceItem from "@/components/EmployeeAdvanceItem.vue"
import ListFiltersActionSheet from "@/components/ListFiltersActionSheet.vue"
import CustomIonModal from "@/components/CustomIonModal.vue"

import useWorkflow from "@/composables/workflow"

const props = defineProps({
	doctype: {
		type: String,
		required: true,
	},
	fields: {
		type: Array,
		required: true,
	},
	groupBy: {
		type: String,
		required: false,
	},
	filterConfig: {
		type: Array,
		required: true,
	},
	tabButtons: {
		type: Array,
		required: true,
	},
	pageTitle: {
		type: String,
		required: true,
	},
})

const listItemComponent = {
	"Leave Application": markRaw(LeaveRequestItem),
	"Expense Claim": markRaw(ExpenseClaimItem),
	"Employee Advance": markRaw(EmployeeAdvanceItem),
}

const router = useRouter()
const socket = inject("$socket")
const employee = inject("$employee")
const filterMap = reactive({})
const activeTab = ref(props.tabButtons[0])
const areFiltersApplied = ref(false)
const appliedFilters = ref([])
const workflowStateField = ref(null)

// infinite scroll
const scrollContainer = ref(null)
const hasNextPage = ref(true)
const listOptions = ref({
	doctype: props.doctype,
	fields: props.fields,
	group_by: props.groupBy,
	order_by: `\`tab${props.doctype}\`.modified desc`,
	page_length: 50,
})

// computed properties
const isTeamRequest = computed(() => {
	return activeTab.value === props.tabButtons[1]
})

const formViewRoute = computed(() => {
	return `${props.doctype.replace(/\s+/g, "")}FormView`
})

const detailViewRoute = computed(() => {
	return `${props.doctype.replace(/\s+/g, "")}DetailView`
})

const defaultFilters = computed(() => {
	const filters = []

	if (isTeamRequest.value) {
		filters.push([props.doctype, "employee", "!=", employee.data.name])
	} else {
		filters.push([props.doctype, "employee", "=", employee.data.name])
	}

	return filters
})

// helper functions
function initializeFilters() {
	props.filterConfig.forEach((filter) => {
		filterMap[filter.fieldname] = {
			condition: "=",
			value: null,
		}
	})

	appliedFilters.value = []
}
initializeFilters()

function prepareFilters() {
	let condition = ""
	let value = ""
	appliedFilters.value = []

	for (const fieldname in filterMap) {
		condition = filterMap[fieldname].condition
		// accessing .value because autocomplete returns an object instead of value
		if (typeof condition === "object" && condition !== null) {
			condition = condition.value
		}

		value = filterMap[fieldname].value
		if (condition && value)
			appliedFilters.value.push([props.doctype, fieldname, condition, value])
	}
}

function applyFilters() {
	prepareFilters()
	fetchDocumentList()
	modalController.dismiss()
	areFiltersApplied.value = appliedFilters.value.length ? true : false
}

function clearFilters() {
	initializeFilters()
	fetchDocumentList()
	modalController.dismiss()
	areFiltersApplied.value = false
}

function fetchDocumentList(start = 0) {
	const filters = [[props.doctype, "docstatus", "!=", "2"]]
	filters.push(...defaultFilters.value)

	if (appliedFilters.value) filters.push(...appliedFilters.value)

	if (workflowStateField.value) {
		listOptions.value.fields.push(workflowStateField.value)
	}

	documents.submit({
		...listOptions.value,
		start: start || 0,
		filters: filters,
	})
}

const documents = createResource({
	url: "frappe.desk.reportview.get",
	onSuccess: (data) => {
		if (data.values?.length < listOptions.value.page_length) {
			hasNextPage.value = false
		}
	},
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

		let pagedData
		if (!documents.params.start || documents.params.start === 0) {
			pagedData = docs
		} else {
			pagedData = documents.data.concat(docs)
		}

		return pagedData
	},
})

const handleScroll = debounce(() => {
	if (!hasNextPage.value) return

	const { scrollTop, scrollHeight, clientHeight } = scrollContainer.value
	const scrollPercentage = (scrollTop / (scrollHeight - clientHeight)) * 100

	if (scrollPercentage >= 90) {
		const start = documents.params.start + listOptions.value.page_length
		fetchDocumentList(start)
	}
}, 500)

const handleRefresh = (event) => {
	setTimeout(() => {
		fetchDocumentList()
		event.target.complete()
	}, 500)
}

watch(
	() => activeTab.value,
	(_value) => {
		hasNextPage.value = true
		fetchDocumentList()
	}
)

onMounted(async () => {
	const workflow = useWorkflow(props.doctype)
	await workflow.workflowDoc.promise
	workflowStateField.value = workflow.getWorkflowStateField()

	hasNextPage.value = true
	fetchDocumentList()

	socket.emit("doctype_subscribe", props.doctype)
	socket.on("list_update", (data) => {
		if (data?.doctype !== props.doctype) return
		fetchDocumentList()
	})
})

onBeforeUnmount(() => {
	socket.off("list_update")
})
</script>
