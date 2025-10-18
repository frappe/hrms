import { toast } from "frappe-ui"

export function useDownloadPDF() {
	async function downloadPDF({ doctype, docname, filename = null }) {
		
		const headers = {
			"X-Frappe-Site-Name": window.location.hostname,
		}
		if (window.csrf_token) {
			headers["X-Frappe-CSRF-Token"] = window.csrf_token
		}

		fetch("/api/method/hrms.api._download_pdf", {
			method: "POST",
			headers,
			body: new URLSearchParams({ doctype: doctype, docname: docname }),
			responseType: "blob",
		}).then((response) => {
				if (response.ok) {
					return response.blob()
				} else {
					toast({
						title: "Download Failed",
						text: `Error downloading PDF`,
						type: "error",
						icon: "alert-circle",
						position: "bottom-center",
						iconClasses: "text-red-500",
					})
				}
			})
			.then((blob) => {
				if (!blob) return
				const blobUrl = window.URL.createObjectURL(blob)
				const link = document.createElement("a")
				link.href = blobUrl
				link.download = `${filename || docname}.pdf`
				link.click()
				setTimeout(() => {
					window.URL.revokeObjectURL(blobUrl)
				}, 3000)
			})
			.catch((error) => {
				toast({
					title: __("Error"),
					text: __("Error downloading PDF", [__(error)]),
					icon: "alert-circle",
					position: "bottom-center",
					iconClasses: "text-red-500",
				})
			})
	}

	return {
		downloadPDF,
	}
}
