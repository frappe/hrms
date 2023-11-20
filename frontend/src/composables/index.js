import { createResource, toast } from "frappe-ui"

function getFileReader() {
	const fileReader = new FileReader()
	const zoneOriginalInstance = fileReader["__zone_symbol__originalInstance"]
	return zoneOriginalInstance || fileReader
}

export class FileAttachment {
	constructor(fileObj) {
		this.fileObj = fileObj
		this.fileName = fileObj.name
	}

	async upload(documentType, documentName, fieldName) {
		return new Promise(async (resolve, reject) => {
			const reader = getFileReader()
			const uploader = createResource({
				url: "hrms.api.upload_base64_file",
				onSuccess: (fileDoc) => resolve(fileDoc),
				onError: (error) => {
					toast({
						title: "Error",
						text: `File upload failed for ${this.fileName}. ${
							error.messages?.[0] || ""
						}`,
						icon: "alert-circle",
						position: "bottom-center",
						iconClasses: "text-red-500",
					})
					reject(error)
				},
			})

			reader.onload = () => {
				console.log("Loaded successfully ✅")
				this.fileContents = reader.result.toString().split(",")[1]

				uploader.submit({
					content: this.fileContents,
					dt: documentType,
					dn: documentName,
					filename: this.fileName,
					fieldname: fieldName,
				})
			}
			reader.readAsDataURL(this.fileObj)
		})
	}

	delete() {
		return createResource({
			url: "hrms.api.delete_attachment",
			onSuccess: () => {
				console.log("Deleted successfully ✅")
			},
			onError: (error) => {
				toast({
					title: "Error",
					text: `File deletion failed. ${error.messages?.[0] || ""}`,
					icon: "alert-circle",
					position: "bottom-center",
					iconClasses: "text-red-500",
				})
			},
		}).submit({
			filename: this.fileName,
		})
	}
}

export async function guessStatusColor(doctype, status) {
	const statesResource = createResource({
		url: "hrms.api.get_doctype_states",
		params: { doctype: doctype },
	})

	const stateMap = await statesResource.reload()

	if (stateMap?.length) {
		if (stateMap?.[status] === "yellow") return "orange"
		return stateMap?.[status]
	}

	let color = "gray"

	if (
		["Open", "Pending", "Unpaid", "Review", "Medium", "Not Approved"].includes(
			status
		)
	) {
		color = "orange"
	} else if (
		["Urgent", "High", "Failed", "Rejected", "Error"].includes(status)
	) {
		color = "red"
	} else if (
		[
			"Closed",
			"Finished",
			"Converted",
			"Completed",
			"Complete",
			"Confirmed",
			"Approved",
			"Yes",
			"Active",
			"Available",
			"Success",
		].includes(status)
	) {
		color = "green"
	} else if (status === "Submitted") {
		color = "blue"
	}

	return color
}
