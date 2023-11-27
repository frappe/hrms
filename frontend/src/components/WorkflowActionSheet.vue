<template>
	<Button
		@click="showTransitions()"
		class="w-full rounded mt-2 py-5 text-base disabled:bg-gray-700 disabled:text-white"
		variant="solid"
	>
		<template #prefix>
			<FeatherIcon name="chevron-up" class="w-4" />
		</template>
		Actions
	</Button>
	<ion-action-sheet
		:buttons="actions"
		:is-open="showActionSheet"
		@didDismiss="applyWorkflow($event)"
	>
	</ion-action-sheet>
</template>

<script setup>
import { IonActionSheet } from "@ionic/vue"
import { computed, ref } from "vue"
import { FeatherIcon } from "frappe-ui"

import useWorkflow from "@/composables/workflow"

const props = defineProps({
	doc: {
		type: Object,
		required: true,
	},
	workflowConfig: {
		type: Object,
		required: false,
	},
})

const emit = defineEmits(["workflow-applied"])

const workflow = computed(() => {
	return props.workflowConfig || useWorkflow(props.doc)
})

let showActionSheet = ref(false)
let actions = ref([])

const showTransitions = async () => {
	const transitions = await workflow.value.getTransitions(props.doc)
	actions.value = transitions.map((transition) => {
		let role = ""
		let actionLabel = transition.toLowerCase()

		if (actionLabel.includes("reject") || actionLabel.includes("cancel")) {
			role = "destructive"
		}

		return {
			text: transition,
			role: role,
			data: {
				action: transition,
			},
		}
	})

	if (actions.value?.length > 0) {
		// always add last action for dismissing the modal
		actions.value.push({
			text: "Dismiss",
			role: "cancel",
		})
		showActionSheet.value = true
	}
}

const applyWorkflow = async (event) => {
	const action = event.detail.data?.action
	if (action) {
		await workflow.value.applyWorkflow(props.doc, action)
		emit("workflow-applied")
	}

	showActionSheet.value = false
}
</script>

<style scoped>
ion-action-sheet {
	--button-color: var(--text-gray-500);
}
</style>
