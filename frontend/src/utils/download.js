// the PDF endpoints stream a file back instead of JSON, so they are called
// with fetch directly rather than through a frappe-ui resource

function getHeaders() {
	const headers = { "X-Frappe-Site-Name": window.location.hostname }
	if (window.csrf_token) {
		headers["X-Frappe-CSRF-Token"] = window.csrf_token
	}
	return headers
}

async function getErrorMessage(response) {
	try {
		const data = await response.json()
		const serverMessages = JSON.parse(data._server_messages || "[]")
		if (serverMessages.length) {
			return JSON.parse(serverMessages[0]).message.replace(/<[^>]*>/g, "")
		}
		return data.exception || response.statusText
	} catch (error) {
		return response.statusText
	}
}

function saveBlob(blob, filename) {
	const blobUrl = window.URL.createObjectURL(blob)
	const link = document.createElement("a")
	link.href = blobUrl
	link.download = filename
	link.click()

	setTimeout(() => {
		window.URL.revokeObjectURL(blobUrl)
	}, 3000)
}

async function downloadFile(url, body, filename) {
	const response = await fetch(url, {
		method: "POST",
		headers: getHeaders(),
		body: new URLSearchParams(body),
	})

	if (!response.ok) throw new Error(await getErrorMessage(response))

	saveBlob(await response.blob(), filename)
}

export function downloadPDF(doctype, docname, filename) {
	return downloadFile(
		"/api/method/hrms.api._download_pdf",
		{ doctype, docname },
		filename || `${docname}.pdf`
	)
}

export function downloadBulkPDF(doctype, docnames, filename) {
	return downloadFile(
		"/api/method/hrms.api._download_bulk_pdf",
		{ doctype, docnames: JSON.stringify(docnames) },
		filename || `${doctype.replace(/ /g, "-")}.pdf`
	)
}
