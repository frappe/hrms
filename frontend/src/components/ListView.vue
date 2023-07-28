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
					<Button icon="filter" appearance="secondary" />
					<router-link :to="{ name: formViewRoute }" v-slot="{ navigate }">
						<Button icon="plus" appearance="primary" @click="navigate" />
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
					<EmptyState message="You have no requests" v-else />
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { useRouter } from "vue-router"
import { inject, ref, markRaw, watch, computed } from "vue"

import { FeatherIcon, createResource } from "frappe-ui"

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
})

const listItemComponent = {
	"Leave Application": markRaw(LeaveRequestItem),
}

const router = useRouter()
const activeTab = ref(props.tabButtons[0])
const employee = inject("$employee")

const isTeamRequest = computed(() => {
	return activeTab.value === props.tabButtons[1]
})

const formViewRoute = computed(() => {
	return `${props.doctype.replace(/\s+/g, "")}FormView`
})

const detailViewRoute = computed(() => {
	return `${props.doctype.replace(/\s+/g, "")}DetailView`
})

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
		const filters = [[props.doctype, "docstatus", "!=", "2"]]

		if (isTeamRequest.value) {
			filters.push([props.doctype, "employee", "!=", employee.data.name])
		} else {
			filters.push([props.doctype, "employee", "=", employee.data.name])
		}

		documents.submit({
			doctype: props.doctype,
			fields: props.fields,
			filters: filters,
		})
	},
	{ immediate: true }
)
</script>
