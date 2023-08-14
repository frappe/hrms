import { createResource } from "frappe-ui"

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

	upload(documentType, documentName, fieldName, successHandler = () => {}) {
		const reader = getFileReader()
		const uploader = createResource({
			url: "hrms.api.upload_base64_file",
			onSuccess: successHandler,
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

		return uploader
	}

	delete() {
		return createResource({
			url: "hrms.api.delete_attachment",
			onSuccess: () => {
				console.log("Deleted successfully ✅")
			},
		}).submit({
			filename: this.fileName,
		})
	}
}
