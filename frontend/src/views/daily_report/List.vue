<template>
	<BaseLayout pageTitle="Daily Reports">
		<template #body>
			<div class="flex flex-col mt-7 mb-7 p-4 gap-5">
				<!-- New Report button -->
				<Button
					id="open-daily-report-modal"
					variant="solid"
					class="w-full py-5 text-base"
				>
					{{ __("New Daily Report") }}
				</Button>

				<!-- Report list -->
				<div v-if="reports.data?.length" class="flex flex-col bg-white rounded divide-y">
					<div
						v-for="report in reports.data"
						:key="report.name"
						class="flex flex-row items-center justify-between p-4 gap-3"
					>
						<div class="flex flex-row items-center gap-3 grow">
							<DailyReportIcon class="h-5 w-5 text-gray-400 shrink-0" />
							<div class="flex flex-col gap-0.5">
								<div class="text-sm font-medium text-gray-800">
									{{ dayjs(report.date).format("D MMM YYYY") }}
								</div>
								<div v-if="report.file" class="text-xs text-gray-500 truncate max-w-[180px]">
									<FeatherIcon name="paperclip" class="h-3 w-3 inline mr-0.5" />
									{{ fileName(report.file) }}
								</div>
							</div>
						</div>
						<Badge
							variant="outline"
							:theme="statusColors[report.status]"
							:label="__(report.status)"
							size="md"
						/>
					</div>
				</div>

				<div v-else-if="!reports.list?.loading" class="flex flex-col items-center py-10 text-gray-400 gap-2">
					<DailyReportIcon class="h-10 w-10" />
					<div class="text-sm">{{ __("No daily reports yet") }}</div>
				</div>
			</div>

			<!-- Create modal -->
			<ion-modal
				ref="modal"
				trigger="open-daily-report-modal"
				:initial-breakpoint="1"
				:breakpoints="[0, 1]"
			>
				<div class="flex flex-col gap-5 p-5 pb-10">
					<div class="text-lg font-bold text-gray-900 mt-2">{{ __("New Daily Report") }}</div>

					<!-- Date -->
					<div class="flex flex-col gap-1.5">
						<label class="text-sm font-medium text-gray-700">{{ __("Date") }}</label>
						<input
							type="date"
							v-model="form.date"
							class="w-full border border-gray-300 rounded px-3 py-2 text-sm text-gray-800 focus:outline-none focus:ring-2 focus:ring-green-700"
						/>
					</div>

					<!-- File picker -->
					<div class="flex flex-col gap-1.5">
						<label class="text-sm font-medium text-gray-700">{{ __("Attachment") }}</label>
						<div v-if="form.selectedFile" class="flex items-center justify-between border border-gray-200 rounded px-3 py-2 bg-gray-50">
							<div class="flex items-center gap-2 min-w-0">
								<FeatherIcon name="paperclip" class="h-4 w-4 text-gray-500 shrink-0" />
								<span class="text-sm text-gray-700 truncate">{{ form.selectedFile.name }}</span>
							</div>
							<button @click="clearFile" class="ml-2 shrink-0">
								<FeatherIcon name="x" class="h-4 w-4 text-gray-500" />
							</button>
						</div>
						<label v-else class="cursor-pointer block">
							<div class="flex flex-col items-center justify-center border-2 border-dashed border-gray-300 rounded p-4 gap-2 hover:border-green-600">
								<FeatherIcon name="upload" class="h-6 w-6 text-gray-400" />
								<span class="text-sm text-gray-500">{{ __("Tap to attach a file") }}</span>
							</div>
							<input
								ref="fileInput"
								type="file"
								class="hidden"
								@change="handleFileSelect"
							/>
						</label>
					</div>

					<ErrorMessage :message="errorMessage" />

					<Button
						variant="solid"
						class="w-full py-5 text-base"
						:loading="submitting"
						@click="submitReport"
					>
						{{ __("Submit Report") }}
					</Button>
				</div>
			</ion-modal>
		</template>
	</BaseLayout>
</template>

<script setup>
import { ref, inject } from "vue"
import { IonModal, modalController } from "@ionic/vue"
import { createResource, Button, Badge, FeatherIcon, ErrorMessage, frappeRequest, toast } from "frappe-ui"

import BaseLayout from "@/components/BaseLayout.vue"
import DailyReportIcon from "@/components/icons/DailyReportIcon.vue"

const dayjs = inject("$dayjs")
const __ = inject("$translate")
const employee = inject("$employee")

const modal = ref(null)
const fileInput = ref(null)
const submitting = ref(false)
const errorMessage = ref("")

const form = ref({
	date: dayjs().format("YYYY-MM-DD"),
	selectedFile: null,
})

const statusColors = {
	Pending: "orange",
	Approved: "green",
	Incomplete: "yellow",
	Rejected: "red",
}

const reports = createResource({
	url: "hr_app.api.get_daily_reports",
	auto: true,
})

function fileName(filePath) {
	return filePath ? filePath.split("/").pop() : ""
}

function handleFileSelect(event) {
	const file = event.target.files[0]
	if (file) form.value.selectedFile = file
}

function clearFile() {
	form.value.selectedFile = null
	if (fileInput.value) fileInput.value.value = ""
}

async function submitReport() {
	if (!form.value.date) {
		errorMessage.value = __("Please select a date.")
		return
	}
	errorMessage.value = ""
	submitting.value = true

	try {
		// Create the Daily Report doc
		const result = await frappeRequest({
			url: "frappe.client.insert",
			method: "POST",
			params: {
				doc: {
					doctype: "Daily Report",
					date: form.value.date,
					employee: employee.data.name,
				},
			},
		})

		const docname = result.name

		// Upload file if selected
		if (form.value.selectedFile) {
			await uploadFile(form.value.selectedFile, docname)
		}

		await reports.reload()
		await modalController.dismiss()

		form.value = { date: dayjs().format("YYYY-MM-DD"), selectedFile: null }
		clearFile()

		toast({
			title: __("Submitted"),
			text: __("Daily report submitted successfully."),
			icon: "check-circle",
			position: "bottom-center",
			iconClasses: "text-green-500",
		})
	} catch (err) {
		const messages = err?.messages || [__("Failed to submit report. Please try again.")]
		errorMessage.value = messages.join("\n")
	} finally {
		submitting.value = false
	}
}

async function uploadFile(file, docname) {
	return new Promise((resolve, reject) => {
		const reader = new FileReader()
		reader.onload = async (e) => {
			const dataUrl = e.target.result
			const base64Content = dataUrl.split(",")[1]
			try {
				await frappeRequest({
					url: "hr_app.api.upload_base64_file",
					method: "POST",
					params: {
						content: base64Content,
						filename: file.name,
						dt: "Daily Report",
						dn: docname,
						fieldname: "file",
					},
				})
				resolve()
			} catch (err) {
				reject(err)
			}
		}
		reader.onerror = reject
		reader.readAsDataURL(file)
	})
}
</script>
