import { computed, ref } from "vue";
import { call, toast } from "frappe-ui";

const GET_FORM =
	"hrms.hr.doctype.employee_onboarding.employee_onboarding_portal.get_onboarding_form";
const SAVE_FORM =
	"hrms.hr.doctype.employee_onboarding.employee_onboarding_portal.save_onboarding_form";
const SUBMIT_FORM =
	"hrms.hr.doctype.employee_onboarding.employee_onboarding_portal.submit_onboarding_form";

const BLOCKED_MESSAGES: Record<string, string> = {
	no_role: "This form is only open to people who were invited to it.",
	no_onboarding: "No onboarding is assigned to this account. Check with your HR contact.",
};

const FULL_WIDTH = "100%";
const HALF_WIDTH = "calc(50% - 0.5rem)";

// Fieldtypes that need the whole row to be readable.
const WIDE_FIELDTYPES = ["Small Text", "Text", "Text Editor"];

interface PortalField {
	fieldname: string;
	fieldtype: string;
	label: string;
	options?: string[];
	reqd?: number;
}

interface PortalSection {
	name: string;
	label: string;
	description?: string;
	fields: PortalField[];
}

interface PortalTable {
	fieldname: string;
	label: string;
	description?: string;
	add_label: string;
	empty_message?: string;
	fields: PortalField[];
}

interface PortalStep {
	name: string;
	label: string;
	sections: string[];
	tables: string[];
	documents?: boolean;
}

interface PortalDocument {
	idx: number;
	document_name: string;
	description?: string;
	required: number;
	attachment?: string;
}

export default async function setup() {
	const loading = ref(true);
	const saving = ref(false);
	const dirty = ref(false);
	const blockedMessage = ref("");
	const stepIndex = ref(0);
	const confirmOpen = ref(false);
	const submitted = ref(false);
	const form = ref<Record<string, any>>({});
	const details = ref<Record<string, any>>({});
	const documents = ref<PortalDocument[]>([]);

	const isReady = computed(() => !loading.value && !blockedMessage.value);
	const isSubmitted = computed(() => submitted.value || Boolean(form.value.is_submitted));
	const isLocked = computed(() => Boolean(form.value.is_locked));
	const isEditable = computed(() => isReady.value && !isLocked.value);
	const showForm = computed(() => isReady.value && !isSubmitted.value);
	const hrContact = computed(() => form.value.hr_contact || "your HR contact");
	const thankYouNote = computed(() => `Wait for further instructions from ${hrContact.value}.`);

	const employeeName = computed(() => form.value.employee_name || "Your details");
	const roleLine = computed(() =>
		[form.value.designation, form.value.company].filter(Boolean).join(" at "),
	);
	const savedNote = computed(() => {
		if (dirty.value) return "You have unsaved changes";
		if (form.value.submitted_on) return `Saved ${formatSavedOn(form.value.submitted_on)}`;
		return "Nothing saved yet";
	});

	const allSteps = computed(() => (form.value.steps || []) as PortalStep[]);
	const sectionsByName = computed(() =>
		Object.fromEntries(
			((form.value.sections || []) as PortalSection[]).map((s) => [s.name, s]),
		),
	);
	const tablesByName = computed(() =>
		Object.fromEntries(
			((form.value.tables || []) as PortalTable[]).map((t) => [t.fieldname, t]),
		),
	);

	const currentStep = computed(() => allSteps.value[stepIndex.value] || null);
	const stepCount = computed(() => allSteps.value.length);
	const isFirstStep = computed(() => stepIndex.value === 0);
	const isLastStep = computed(() => stepIndex.value === stepCount.value - 1);
	const stepCounter = computed(() => `Step ${stepIndex.value + 1} of ${stepCount.value}`);
	const currentStepLabel = computed(() => currentStep.value?.label || "");
	const nextLabel = computed(() => (isLastStep.value ? "Submit" : "Save and continue"));

	/** Markers for the rail. `done` means every required item in that step is filled. */
	const stepMarkers = computed(() =>
		allSteps.value.map((step, index) => {
			const done = isStepDone(step);
			const isCurrent = index === stepIndex.value;
			// Colour goes through styles, not classes: block classes are not evaluated for
			// {{ }} expressions, only props and styles are.
			return {
				key: step.name,
				index,
				label: step.label,
				number: String(index + 1),
				isCurrent,
				isDone: done && !isCurrent,
				markerBg: isCurrent
					? "var(--surface-gray-9)"
					: done
					  ? "var(--surface-green-2)"
					  : "transparent",
				markerBorder: isCurrent
					? "var(--surface-gray-9)"
					: done
					  ? "var(--surface-green-2)"
					  : "var(--outline-gray-2)",
				markerColor: isCurrent
					? "var(--ink-green-1)"
					: done
					  ? "var(--ink-green-8)"
					  : "var(--ink-gray-5)",
				labelColor: isCurrent ? "var(--ink-gray-8)" : "var(--ink-gray-5)",
				labelWeight: isCurrent ? "500" : "400",
			};
		}),
	);

	/**
	 * Done means required items are satisfied AND the step holds something. Without the
	 * second half, a step with no required field would show as done before it is opened.
	 */
	function isStepDone(step: PortalStep) {
		if (step.documents) {
			if (!documents.value.length) return false;
			return documents.value.every((row) => !row.required || row.attachment);
		}

		const fields = step.sections.flatMap((name) => sectionsByName.value[name]?.fields || []);
		const requiredFilled = fields
			.filter((field) => field.reqd)
			.every((field) => !isBlank(details.value[field.fieldname]));
		const hasAnyValue =
			fields.some((field) => !isBlank(details.value[field.fieldname])) ||
			step.tables.some((table) => (details.value[table] || []).length);

		return requiredFilled && hasAnyValue;
	}

	const sectionCards = computed(() =>
		(currentStep.value?.sections || [])
			.map((name) => sectionsByName.value[name])
			.filter(Boolean)
			.map((section) => ({
				key: section.name,
				label: section.label,
				description: section.description || "",
				fields: section.fields.map((field) =>
					fieldEntry(field, details.value[field.fieldname], {
						key: `${section.name}.${field.fieldname}`,
						fieldname: field.fieldname,
					}),
				),
			})),
	);

	/**
	 * Repeaters nest here. A nested Repeater's own props are evaluated in the OUTER slot
	 * scope, so `{{ dataItem.fields }}` still reads the section; only the inner slot's
	 * `dataItem` is shadowed. Each entry therefore carries the table and index it writes to.
	 */
	const tableCards = computed(() =>
		(currentStep.value?.tables || [])
			.map((name) => tablesByName.value[name])
			.filter(Boolean)
			.map((table) => {
				const rows = (details.value[table.fieldname] || []) as Record<string, any>[];
				return {
					key: table.fieldname,
					table: table.fieldname,
					label: table.label,
					description: table.description || "",
					addLabel: table.add_label,
					emptyMessage: table.empty_message || "Nothing added yet.",
					isEmpty: rows.length === 0,
					count: rows.length,
					rows: rows.map((row, index) => ({
						key: `${table.fieldname}.${index}`,
						table: table.fieldname,
						index,
						title: rowTitle(table, row, index),
						fields: table.fields.map((field) =>
							fieldEntry(field, row[field.fieldname], {
								key: `${table.fieldname}.${index}.${field.fieldname}`,
								table: table.fieldname,
								index,
								fieldname: field.fieldname,
							}),
						),
					})),
				};
			}),
	);

	const documentRows = computed(() => {
		if (!currentStep.value?.documents) return [];
		return documents.value.map((row) => ({
			key: `doc.${row.idx}`,
			idx: row.idx,
			label: row.document_name,
			description: row.description || "",
			fileName: row.attachment ? row.attachment.split("/").pop() : "",
			statusLabel: row.attachment ? "Uploaded" : row.required ? "Required" : "Optional",
			statusTheme: row.attachment ? "green" : row.required ? "orange" : "gray",
			buttonLabel: row.attachment ? "Replace" : "Upload",
			buttonVariant: row.attachment ? "ghost" : "subtle",
		}));
	});

	const showDocuments = computed(() => Boolean(currentStep.value?.documents));

	function fieldEntry(field: PortalField, value: any, extra: Record<string, any>) {
		return {
			label: field.label,
			controlType: controlTypeFor(field),
			options: field.options || [],
			required: Boolean(field.reqd),
			value: value ?? "",
			width: WIDE_FIELDTYPES.includes(field.fieldtype) ? FULL_WIDTH : HALF_WIDTH,
			...extra,
		};
	}

	function controlTypeFor(field: PortalField) {
		if (field.fieldtype === "Select") return "select";
		if (field.fieldtype === "Date") return "date";
		if (field.fieldtype === "Int" || field.fieldtype === "Currency") return "number";
		if (WIDE_FIELDTYPES.includes(field.fieldtype)) return "textarea";
		return "text";
	}

	function rowTitle(table: PortalTable, row: Record<string, any>, index: number) {
		const lead = table.fields[0].fieldname;
		const second = table.fields[1].fieldname;
		return row[second] || row[lead] || `${table.label} ${index + 1}`;
	}

	function isBlank(value: any) {
		return value === null || value === undefined || value === "";
	}

	function formatSavedOn(value: string) {
		const date = new Date(value.replace(" ", "T"));
		if (Number.isNaN(date.getTime())) return value;
		return date.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
	}

	async function load() {
		loading.value = true;
		try {
			const response = await call(GET_FORM);
			if (!response?.allowed) {
				blockedMessage.value =
					BLOCKED_MESSAGES[response?.reason] || BLOCKED_MESSAGES.no_onboarding;
				return;
			}
			form.value = response;
			details.value = response.details || {};
			documents.value = response.documents || [];
			dirty.value = false;
		} catch (error: any) {
			blockedMessage.value = error?.messages?.[0] || "This form could not be opened.";
		} finally {
			loading.value = false;
		}
	}

	function setField(entry: Record<string, any>, value: any) {
		dirty.value = true;
		if (entry.table === undefined) {
			details.value = { ...details.value, [entry.fieldname]: value };
			return;
		}

		const rows = [...(details.value[entry.table] || [])];
		rows[entry.index] = { ...rows[entry.index], [entry.fieldname]: value };
		details.value = { ...details.value, [entry.table]: rows };
	}

	function addRow(table: string) {
		dirty.value = true;
		details.value = { ...details.value, [table]: [...(details.value[table] || []), {}] };
	}

	function removeRow(table: string, index: number) {
		dirty.value = true;
		const rows = (details.value[table] || []).filter((_: unknown, i: number) => i !== index);
		details.value = { ...details.value, [table]: rows };
	}

	function setDocument(idx: number, fileUrl: string) {
		dirty.value = true;
		documents.value = documents.value.map((row) =>
			row.idx === idx ? { ...row, attachment: fileUrl } : row,
		);
	}

	function scrollToTop() {
		document.querySelector(".ed-scroll")?.scrollTo({ top: 0, behavior: "smooth" });
	}

	async function goToStep(index: number) {
		if (index === stepIndex.value) return;
		if (dirty.value) await save({ silent: true });
		stepIndex.value = Math.max(0, Math.min(index, stepCount.value - 1));
		scrollToTop();
	}

	function goBack() {
		stepIndex.value = Math.max(0, stepIndex.value - 1);
		scrollToTop();
	}

	async function goNext() {
		if (isLastStep.value) {
			await save({ silent: true });
			confirmOpen.value = true;
			return;
		}

		await save({ silent: true });
		stepIndex.value = stepIndex.value + 1;
		scrollToTop();
	}

	function setConfirmOpen(value: boolean) {
		confirmOpen.value = value;
	}

	async function confirmSubmit() {
		if (saving.value || !isEditable.value) return;

		saving.value = true;
		try {
			const response = await call(SUBMIT_FORM, {
				details: JSON.stringify(details.value),
				documents: JSON.stringify(
					documents.value.map((row) => ({ idx: row.idx, attachment: row.attachment })),
				),
			});
			form.value = {
				...form.value,
				confirmed_on: response?.confirmed_on,
				is_submitted: true,
			};
			dirty.value = false;
			submitted.value = true;
			confirmOpen.value = false;
			scrollToTop();
		} catch (error: any) {
			toast.error(error?.messages?.[0] || "Could not submit your details");
		} finally {
			saving.value = false;
		}
	}

	async function logout() {
		await call("logout");
		window.location.href = "/login";
	}

	async function save(options: { silent?: boolean } = {}) {
		if (saving.value || !isEditable.value) return;

		saving.value = true;
		try {
			const response = await call(SAVE_FORM, {
				details: JSON.stringify(details.value),
				documents: JSON.stringify(
					documents.value.map((row) => ({ idx: row.idx, attachment: row.attachment })),
				),
			});
			form.value = { ...form.value, submitted_on: response?.submitted_on };
			dirty.value = false;
			if (!options.silent) toast.success("Your details were saved");
		} catch (error: any) {
			toast.error(error?.messages?.[0] || "Could not save your details");
		} finally {
			saving.value = false;
		}
	}

	await load();

	return {
		loading,
		saving,
		dirty,
		blockedMessage,
		form,
		isReady,
		isLocked,
		isEditable,
		isSubmitted,
		showForm,
		confirmOpen,
		hrContact,
		thankYouNote,
		employeeName,
		roleLine,
		savedNote,
		stepMarkers,
		stepIndex,
		stepCount,
		stepCounter,
		currentStepLabel,
		isFirstStep,
		isLastStep,
		nextLabel,
		sectionCards,
		tableCards,
		documentRows,
		showDocuments,
		setField,
		addRow,
		removeRow,
		setDocument,
		goToStep,
		goBack,
		goNext,
		save,
		setConfirmOpen,
		confirmSubmit,
		logout,
	};
}
