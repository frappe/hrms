import { createResource, toast } from "frappe-ui"
import { computed } from "vue"
import { userResource } from "@/data/user"

export default function useWorkflow(doctype) {
	const workflowDoc = createResource({
		url: "hrms.api.get_workflow",
		params: { doctype: doctype },
		cache: ["hrms:workflow", doctype],
	})
	workflowDoc.reload()

	const hasWorkflow = computed(() => {
		const workflowData = workflowDoc?.data
		return Boolean(Object.keys(workflowData || {}).length > 0)
	})

	const getWorkflowStateField = () => {
		// NOTE: checkbox labelled 'Don't Override Status' is named override_status hence the inverted logic
		return !workflowDoc.data?.override_status
			? workflowDoc.data?.workflow_state_field
			: ""
	}

	const getDefaultState = (docstatus) => {
		return workflowDoc.data?.states.find(
			(state) => state.doc_status == docstatus
		)
	}

	const getTransitions = async (doc) => {
		const transitions = createResource({
			url: "frappe.model.workflow.get_transitions",
			params: { doc: doc },
			transform: (data) => {
				const isSelfApproval = userResource?.data?.name == doc.owner

				return data
					.filter(
						(transition) => transition.allow_self_approval || !isSelfApproval
					)
					.map((transition) => transition.action)
			},
		})

		return await transitions.reload()
	}

	const getDocumentStateRoles = (state) => {
		return workflowDoc.data?.states
			.filter((s) => s.state == state)
			.map((s) => s.allow_edit)
	}

	const isReadOnly = (doc) => {
		const state_fieldname = workflowDoc.data?.workflow_state_field
		if (!state_fieldname) return false

		const state = doc[state_fieldname] || getDefaultState(doc.docstatus)

		const roles = getDocumentStateRoles(state)
		return !roles.some((role) => userResource.data.roles.includes(role))
	}

	const applyWorkflow = async (doc, action) => {
		const applyWorkflow = createResource({
			url: "frappe.model.workflow.apply_workflow",
			params: { doc: doc, action: action },
			onSuccess() {
				toast({
					title: "Success",
					text: `Workflow action '${action}' applied successfully`,
					icon: "check-circle",
					position: "bottom-center",
					iconClasses: "text-green-500",
				})
			},
			onError() {
				toast({
					title: "Error",
					text: `Error applying workflow action: ${action}`,
					icon: "alert-circle",
					position: "bottom-center",
					iconClasses: "text-red-500",
				})
				console.log(`Error applying workflow action: ${action}`)
			},
		})
		await applyWorkflow.reload()
	}

	return {
		hasWorkflow,
		workflowDoc,
		getWorkflowStateField,
		getTransitions,
		getDocumentStateRoles,
		isReadOnly,
		applyWorkflow,
	}
}
