<template>
	<div class="flex flex-col h-screen w-screen">
		<div class="w-full sm:w-96">
			<header
				class="flex flex-row gap-1 bg-white shadow-sm py-4 px-2 items-center border-b"
			>
				<Button appearance="minimal" class="!px-0 !py-0" @click="router.back()">
					<FeatherIcon name="chevron-left" class="h-5 w-5" />
				</Button>
				<h2 class="text-2xl font-semibold text-gray-900">
					{{ `New ${doctype}` }}
				</h2>
			</header>

			<div class="flex flex-col space-y-4 bg-white p-4">
				<FormField
					v-for="field in formFields.data"
					:key="field.name"
					:fieldtype="field.fieldtype"
					:fieldname="field.fieldname"
					v-model="field.fieldname"
					:default="field.default"
					:label="field.label"
					:options="field.options"
					:readOnly="Boolean(field.read_only)"
					:reqd="Boolean(field.reqd)"
				/>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue"
import { useRouter } from "vue-router"
import { createResource, FeatherIcon } from "frappe-ui"
import FormField from "@/components/FormField.vue"

const props = defineProps({
	doctype: {
		type: String,
		required: true,
	},
	id: {
		type: String,
		required: false,
	},
})

const router = useRouter()

const formFields = createResource({
	url: "hrms.api.get_doctype_fields",
	params: {
		doctype: props.doctype,
	},
})
formFields.reload()
</script>
