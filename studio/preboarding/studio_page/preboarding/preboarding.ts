import { computed, ref } from "vue";
import { buildLayoutFromMeta } from "@framework/ui/FormLayout";

const TABS_NOT_ON_PAGE = ["documents_tab", "request_tab"];
const DOCUMENTS_STEP = "Documents";
const REVIEW_STEP = "Review";

export default function setup(context) {
	const { request, step, toast } = context;
	const boot = window.boot || {};
	const formTabs = getFormTabs(boot);
	const saving = ref(false);

	const documents = computed(() => request?.doc?.documents ?? []);
	const steps = computed(() => [
		...formTabs.map((tab) => tab.label),
		...(documents.value.length ? [DOCUMENTS_STEP] : []),
		REVIEW_STEP,
	]);
	const stepTitle = computed(() => steps.value[step.value]);
	const isFormStep = computed(() => step.value < formTabs.length);
	const isReviewStep = computed(() => stepTitle.value === REVIEW_STEP);
	const missing = computed(() => [...getMissingFields(), ...getMissingDocuments()]);

	function getMissingFields() {
		const doc = request?.doc || {};
		return formTabs
			.flatMap((tab) =>
				tab.sections.flatMap((section) => section.columns.flatMap((col) => col.fields)),
			)
			.filter((field) => field.reqd && isEmpty(doc[field.fieldname]))
			.map((field) => field.label);
	}

	function getMissingDocuments() {
		return documents.value
			.filter((row) => row.required && !row.attachment)
			.map((row) => row.document_name);
	}

	async function save() {
		saving.value = true;
		try {
			await request.save.submit();
			return true;
		} catch (error) {
			toast.error(getErrorMessage(error));
			return false;
		} finally {
			saving.value = false;
		}
	}

	async function next() {
		if (!(await save())) return;
		step.value += 1;
		window.scrollTo({ top: 0 });
	}

	async function submitDetails() {
		if (!(await save())) return;
		try {
			await request.submit_details.submit();
			await request.reload();
			toast.success("Your details are with HR now");
		} catch (error) {
			toast.error(getErrorMessage(error));
		}
	}

	return {
		saving,
		steps,
		stepTitle,
		isFormStep,
		isReviewStep,
		missing,
		isDocumentsStep: computed(() => stepTitle.value === DOCUMENTS_STEP),
		currentLayout: computed(() =>
			isFormStep.value ? [{ ...formTabs[step.value], label: "" }] : [],
		),
		stepCaption: computed(() => `Step ${step.value + 1} of ${steps.value.length}`),
		progressValue: computed(() => ((step.value + 1) / steps.value.length) * 100),
		primaryLabel: computed(() => (isReviewStep.value ? "Submit" : "Next")),
		missingSummary: computed(() => missing.value.join(", ")),
		submittedTitle: computed(() => getSubmittedTitle(request?.doc?.submitted_on)),
		primaryAction: () => (isReviewStep.value ? submitDetails() : next()),
		back: () => (step.value -= 1),
		attachDocument: (row, file) => {
			row.attachment = file.file_url;
			save();
		},
	};
}

function getFormTabs(boot) {
	if (!boot.fields) return [];
	return buildLayoutFromMeta(boot.fields, { childMetas: boot.child_metas }).filter(
		(tab) => !TABS_NOT_ON_PAGE.includes(tab.name),
	);
}

function getSubmittedTitle(submittedOn) {
	if (!submittedOn) return "";
	return `Submitted on ${new Date(submittedOn.replace(" ", "T")).toLocaleDateString()}`;
}

function isEmpty(value) {
	return value == null || value === "" || (Array.isArray(value) && !value.length);
}

function getErrorMessage(error) {
	return error?.messages?.[0] || error?.message || "Something went wrong. Try again.";
}
