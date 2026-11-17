import { computed, ref } from "vue";
import { buildLayoutFromMeta } from "@framework/ui/FormLayout";

const TABS_NOT_ON_PAGE = ["documents_tab", "request_tab"];
const FIELDS_NOT_ON_PAGE = ["bio"];
const DOCUMENTS_SECTION = "Documents";
const DONE = "Done";
const IN_PROGRESS = "In progress";
const NOT_STARTED = "Not started";
const PHOTO_FIELD = "image";
const MONTHS = [
	"Jan",
	"Feb",
	"Mar",
	"Apr",
	"May",
	"Jun",
	"Jul",
	"Aug",
	"Sep",
	"Oct",
	"Nov",
	"Dec",
];
const BLANK_LABEL = "\u00a0";
const ENTRY_TABLES = {
	education: {
		label: "education",
		layout: () => getEducationLayout(),
		isComplete: (row) => Boolean(row.qualification && row.school_univ),
		title: (row) => row.qualification || row.school_univ,
		subtitle: (row) => [row.school_univ, row.level, row.year_of_passing],
	},
	external_work_history: {
		label: "work experience",
		layout: (row) => getWorkLayout(row),
		isComplete: (row) => Boolean(row.designation && row.company_name),
		title: (row) => row.designation || row.company_name,
		subtitle: (row) => [
			row.company_name,
			row.total_experience && `${row.total_experience} years`,
		],
	},
};

export default function setup(context) {
	const { request, openSection, toast } = context;
	const boot = window.boot || {};
	const formTabs = getFormTabs(boot);
	const job = boot.job || {};
	const saving = ref(false);
	const dialogOpen = ref(false);
	const submitOpen = ref(false);
	const dialogTable = ref(null);
	const dialogIndex = ref(null);
	const dialogRow = ref({});
	const continued = ref(new Set());

	const documents = computed(() => request?.doc?.documents ?? []);
	const documentsIndex = formTabs.length;
	const isSubmitted = computed(() => Boolean(request?.doc?.submitted_on));
	const sectionCount = computed(() => formTabs.length + (documents.value.length ? 1 : 0));

	const sections = computed(() => [
		...formTabs.map((tab, index) => ({ label: tab.label, status: getStatus(index) })),
		{ label: DOCUMENTS_SECTION, status: getStatus(documentsIndex) },
	]);
	const doneCount = computed(
		() => sections.value.slice(0, sectionCount.value).filter((s) => s.status === DONE).length,
	);
	const missingCount = computed(
		() =>
			formTabs.reduce((count, tab, index) => count + getMissingFields(index).length, 0) +
			getMissingDocuments().length,
	);

	function getMissingFields(index) {
		const doc = request?.doc || {};
		return getFields([formTabs[index]]).filter(
			(field) => field.reqd && isEmpty(doc[field.fieldname]),
		);
	}

	function getMissingDocuments() {
		return documents.value
			.filter((row) => row.required && !row.attachment)
			.map((row) => row.document_name);
	}

	function getStatus(index) {
		if (isSubmitted.value) return DONE;
		const doc = request?.doc || {};
		const isDocuments = index === documentsIndex;
		const missing = isDocuments
			? getMissingDocuments().length
			: getMissingFields(index).length;
		const started = isDocuments
			? documents.value.some((row) => row.attachment)
			: getFields([formTabs[index]]).some((field) => !isEmpty(doc[field.fieldname]));
		if (!missing && (started || continued.value.has(index))) return DONE;
		return started ? IN_PROGRESS : NOT_STARTED;
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

	function checkSection(index) {
		const fields = getMissingFields(index);
		if (!fields.length) return true;
		openSection.value = index;
		toast.error(`Fill in ${fields.map((field) => field.label).join(", ")}`);
		focusField(fields[0].fieldname);
		return false;
	}

	async function continueSection(index) {
		if (index < formTabs.length) {
			if (!checkSection(index)) return;
			if (!(await save())) return;
		}
		continued.value = new Set(continued.value).add(index);
		const next = index + 1 < sectionCount.value ? index + 1 : -1;
		openSection.value = next;
		if (next >= 0) scrollToSection(next);
	}

	function confirmSubmit() {
		if (!formTabs.every((tab, index) => checkSection(index))) return;
		const missing = getMissingDocuments();
		if (missing.length) {
			openSection.value = documentsIndex;
			toast.error(`Upload ${missing.join(", ")}`);
			return;
		}
		submitOpen.value = true;
	}

	async function submitDetails() {
		submitOpen.value = false;
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
		dialogRow.value = toDialogRow(index === null ? {} : request.doc[fieldname][index]);
		dialogOpen.value = true;
	}

	async function saveRow() {
		const row = fromDialogRow(dialogRow.value);
		const rows = [...(request.doc[dialogTable.value] || [])];
		if (dialogIndex.value === null) rows.push(row);
		else rows[dialogIndex.value] = row;
		if (await save({ [dialogTable.value]: rows })) dialogOpen.value = false;
	}

	return {
		saving,
		dialogOpen,
		submitOpen,
		dialogRow,
		isSubmitted,
		sections,
		documentsIndex,
		hasDocuments: computed(() => documents.value.length > 0),
		employeeName: computed(() => {
			const doc = request?.doc || {};
			const name = [doc.first_name, doc.middle_name, doc.last_name]
				.filter(Boolean)
				.join(" ");
			return name || "Your details";
		}),
		designation: job.designation || "",
		joiningLabel: job.date_of_joining ? `Joining ${formatDate(job.date_of_joining)}` : "",
		department: job.department || "",
		branch: job.branch || "",
		progressLabel: computed(() => `${doneCount.value} of ${sectionCount.value} sections done`),
		submitHint: computed(() => {
			const count = missingCount.value;
			if (!count) return "Ready to submit";
			return `Add ${count} required ${count === 1 ? "item" : "items"} to submit`;
		}),
		canSubmit: computed(() => !missingCount.value && !isSubmitted.value),
		sectionLayout: (index) => (formTabs[index] ? [getPageTab(formTabs[index])] : []),
		toggleSection: (index) => {
			openSection.value = openSection.value === index ? -1 : index;
		},
		continueSection,
		confirmSubmit,
		dialogTitle: computed(() => {
			const label = ENTRY_TABLES[dialogTable.value]?.label;
			return dialogIndex.value === null ? `Add ${label}` : `Edit ${label}`;
		}),
		dialogLayout: computed(
			() => ENTRY_TABLES[dialogTable.value]?.layout(dialogRow.value) ?? [],
		),
		dialogActions: computed(() => [
			{ label: "Cancel", onClick: () => (dialogOpen.value = false) },
			{
				label: "Save",
				variant: "solid",
				loading: saving.value,
				disabled: !ENTRY_TABLES[dialogTable.value]?.isComplete(dialogRow.value),
				onClick: () => saveRow(),
			},
		]),
		submitActions: [
			{ label: "Submit", variant: "solid", onClick: () => submitDetails() },
			{ label: "Cancel", onClick: () => (submitOpen.value = false) },
		],
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
		fileName: (url) => url.split("/").pop(),
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
		field.fieldname === PHOTO_FIELD ||
		field.fieldname in ENTRY_TABLES ||
		FIELDS_NOT_ON_PAGE.includes(field.fieldname);
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

function getEducationLayout() {
	return dialogLayout([
		[
			[
				{
					fieldname: "qualification",
					label: "Qualification",
					placeholder: "e.g. Bachelor of Science",
				},
				{
					fieldname: "school_univ",
					label: "School or university",
					placeholder: "Name of your school or university",
				},
				select("level", "Level", ["Under Graduate", "Graduate", "Post Graduate"]),
				select("year_of_passing", "Year of passing", getYears()),
			],
		],
	]);
}

function getWorkLayout(row) {
	const toDate = [
		[select("to_month", "To", MONTHS, "Month")],
		[select("to_year", BLANK_LABEL, getYears(), "Year")],
	];
	return dialogLayout([
		[
			[
				{ fieldname: "designation", label: "Designation" },
				{ fieldname: "company_name", label: "Company" },
			],
		],
		[
			[select("from_month", "From", MONTHS, "Month")],
			[select("from_year", BLANK_LABEL, getYears(), "Year")],
		],
		...(row.currently_working ? [] : [toDate]),
		[[{ fieldname: "currently_working", fieldtype: "Check", label: "I work here now" }]],
	]);
}

function dialogLayout(sections) {
	return [
		{
			sections: sections.map((columns) => ({
				hideLabel: true,
				hideBorder: true,
				columns: columns.map((fields) => ({
					fields: fields.map((field) => ({ fieldtype: "Data", ...field })),
				})),
			})),
		},
	];
}

function select(fieldname, label, options, placeholder) {
	return {
		fieldname,
		label,
		fieldtype: "Select",
		options: ["", ...options].join("\n"),
		placeholder,
	};
}

function getYears() {
	const year = new Date().getFullYear() + 5;
	return Array.from({ length: 60 }, (_, index) => String(year - index));
}

function toDialogRow(row) {
	return { ...row, year_of_passing: row.year_of_passing ? String(row.year_of_passing) : "" };
}

function fromDialogRow(row) {
	const { from_month, from_year, to_month, to_year, currently_working, ...values } = row;
	const months = getMonthsBetween(
		from_month,
		from_year,
		currently_working ? null : [to_month, to_year],
	);
	if (months !== null) values.total_experience = String(Math.round((months / 12) * 10) / 10);
	return values;
}

function getMonthsBetween(fromMonth, fromYear, to) {
	if (!fromMonth || !fromYear) return null;
	const now = new Date();
	const [toMonth, toYear] = to ?? [MONTHS[now.getMonth()], String(now.getFullYear())];
	if (!toMonth || !toYear) return null;
	const months =
		(Number(toYear) - Number(fromYear)) * 12 +
		MONTHS.indexOf(toMonth) -
		MONTHS.indexOf(fromMonth) +
		1;
	return Math.max(months, 0);
}

function getFields(tabs) {
	return tabs.flatMap((tab) =>
		tab.sections.flatMap((section) => section.columns.flatMap((col) => col.fields)),
	);
}

function focusField(fieldname) {
	setTimeout(() => {
		const field = document.querySelector(`[data-fieldname="${fieldname}"]`);
		field?.scrollIntoView({ block: "center" });
		field?.querySelector("input, textarea, button")?.focus();
	});
}

function scrollToSection(index) {
	setTimeout(() => {
		document
			.querySelector(`.pb-section-${index}`)
			?.scrollIntoView({ behavior: "smooth", block: "start" });
	});
}

function formatDate(value) {
	return new Date(`${value}T00:00:00`).toLocaleDateString(undefined, {
		weekday: "short",
		day: "numeric",
		month: "short",
	});
}

function isEmpty(value) {
	return value == null || value === "" || (Array.isArray(value) && !value.length);
}

function getErrorMessage(error) {
	return error?.messages?.[0] || error?.message || "Something went wrong. Try again.";
}
