import { createResource } from "frappe-ui"
import { ref, computed } from "vue"
import { userResource } from "@/data/user"

export default function useWorkflow(doctype) {
	const workflow = ref({})

	const workflowDoc = createResource({
		url: "hrms.api.get_workflow",
		params: { doctype: doctype },
		cache: `Workflow:${doctype}`,
		onSuccess: (data) => {
			console.log("Workflow loaded successfully ✅", data)
			workflow.value = data
		},
	})
	workflowDoc.reload()

	const getDefaultState = (docstatus) => {
		return workflow.value.states.find((state) => state.doc_status == docstatus)
	}

	const getTransitions = (doc) => {}

	const getDocumentStateRoles = (state) => {
		return workflow.value.states
			.filter((s) => s.state == state)
			.map((s) => s.allow_edit)
	}

	const isReadOnly = (doc) => {
		const state_fieldname = workflow.value.workflow_state_field
		if (!state_fieldname) return false

		const state = doc[state_fieldname] || getDefaultState(doc.docstatus)

		const roles = getDocumentStateRoles(state)
		return !roles.some((role) => userResource.data.roles.includes(role.role))
	}

	return {
		workflow,
		getTransitions,
		getDocumentStateRoles,
		isReadOnly,
	}
}