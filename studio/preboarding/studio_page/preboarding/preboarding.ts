import { computed, ref } from "vue";
import { buildLayoutFromMeta } from "@framework/ui/FormLayout";

const TABS_NOT_ON_PAGE = ["documents_tab", "request_tab"];
const DOCUMENTS_STEP = "Documents";
const REVIEW_STEP = "Review";
const PHOTO_FIELD = "image";
const ENTRY_TABLES = {
	education: {
		label: "education",
		title: (row) => row.qualification || row.school_univ,
		subtitle: (row) => [row.school_univ, row.level, row.year_of_passing],
	},
	external_work_history: {
		label: "work experience",
		title: (row) => row.designation || row.company_name,
		subtitle: (row) => [
			row.company_name,
			row.total_experience && `${row.total_experience} years`,
		],
	},
};

export default function setup(context) {
	const { request, step, toast } = context;
	const boot = window.boot || {};
	const formTabs = getFormTabs(boot);
	const saving = ref(false);
	const dialogOpen = ref(false);
	const dialogTable = ref(null);
	const dialogIndex = ref(null);
	const dialogRow = ref({});

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
		return getFields(formTabs)
			.filter((field) => field.reqd && isEmpty(doc[field.fieldname]))
			.map((field) => field.label);
	}

	function getMissingDocuments() {
		return documents.value
			.filter((row) => row.required && !row.attachment)
			.map((row) => row.document_name);
	}

	async function save(values) {
		saving.value = true;
		try {
			await (values ? request.setValue.submit(values) : request.save.submit());
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
			toast.success("Your details have been submitted");
		} catch (error) {
			toast.error(getErrorMessage(error));
		}
	}

	function openRow(fieldname, index = null) {
		dialogTable.value = fieldname;
		dialogIndex.value = index;
		dialogRow.value = index === null ? {} : { ...request.doc[fieldname][index] };
		dialogOpen.value = true;
	}

	async function saveRow() {
		const rows = [...(request.doc[dialogTable.value] || [])];
		if (dialogIndex.value === null) rows.push(dialogRow.value);
		else rows[dialogIndex.value] = dialogRow.value;
		if (await save({ [dialogTable.value]: rows })) dialogOpen.value = false;
	}

	return {
		saving,
		steps,
		stepTitle,
		isFormStep,
		isReviewStep,
		missing,
		dialogOpen,
		dialogRow,
		isDocumentsStep: computed(() => stepTitle.value === DOCUMENTS_STEP),
		isSubmitted: computed(() => Boolean(request?.doc?.submitted_on)),
		currentLayout: computed(() =>
			isFormStep.value ? [getPageTab(formTabs[step.value])] : [],
		),
		currentTables: computed(() =>
			isFormStep.value
				? getFields([formTabs[step.value]])
						.map((field) => field.fieldname)
						.filter((fieldname) => fieldname in ENTRY_TABLES)
				: [],
		),
		stepCaption: computed(() => `Step ${step.value + 1} of ${steps.value.length}`),
		progressValue: computed(() => ((step.value + 1) / steps.value.length) * 100),
		primaryLabel: computed(() => (isReviewStep.value ? "Submit" : "Next")),
		missingSummary: computed(() => missing.value.join(", ")),
		dialogTitle: computed(() => {
			const label = ENTRY_TABLES[dialogTable.value]?.label;
			return dialogIndex.value === null ? `Add ${label}` : `Edit ${label}`;
		}),
		dialogLayout: computed(() => getEntryLayout(boot, dialogTable.value)),
		dialogActions: computed(() => [
			{ label: "Save", variant: "solid", loading: saving.value, onClick: () => saveRow() },
		]),
		primaryAction: () => (isReviewStep.value ? submitDetails() : next()),
		back: () => (step.value -= 1),
		rowTitle: (fieldname, row) => ENTRY_TABLES[fieldname].title(row) || "Untitled",
		rowSubtitle: (fieldname, row) =>
			ENTRY_TABLES[fieldname].subtitle(row).filter(Boolean).join(" · "),
		openRow,
		removeRow: (fieldname, index) =>
			save({ [fieldname]: request.doc[fieldname].filter((row, i) => i !== index) }),
		setPhoto: (file) => save({ [PHOTO_FIELD]: file.file_url }),
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

function getPageTab(tab) {
	const isShownElsewhere = (field) =>
		field.fieldname === PHOTO_FIELD || field.fieldname in ENTRY_TABLES;
	const sections = tab.sections
		.map((section) => ({
			...section,
			columns: section.columns.map((col) => ({
				...col,
				fields: col.fields.filter((field) => !isShownElsewhere(field)),
			})),
		}))
		.filter((section) => section.columns.some((col) => col.fields.length));
	return { ...tab, label: "", sections };
}

function getEntryLayout(boot, fieldname) {
	const options = boot.fields?.find((field) => field.fieldname === fieldname)?.options;
	if (!options) return [];
	return buildLayoutFromMeta(boot.child_metas[options]).map((tab) => ({ ...tab, label: "" }));
}

function getFields(tabs) {
	return tabs.flatMap((tab) =>
		tab.sections.flatMap((section) => section.columns.flatMap((col) => col.fields)),
	);
}

function isEmpty(value) {
	return value == null || value === "" || (Array.isArray(value) && !value.length);
}

function getErrorMessage(error) {
	return error?.messages?.[0] || error?.message || "Something went wrong. Try again.";
}
