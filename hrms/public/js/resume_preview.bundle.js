import * as pdfjs from "pdfjs-dist/build/pdf.mjs";

frappe.provide("hrms");

pdfjs.GlobalWorkerOptions.workerSrc = frappe.assets.bundled_asset(
	"resume_preview_worker.bundle.js",
);

const MAX_PAGES = 10;

/** Draws the PDF at `url` into `container`, one canvas per page (up to 10); resolves with { page_count }. */
hrms.render_resume_preview = async (container, url) => {
	const task = pdfjs.getDocument({ url });
	try {
		const pdf = await task.promise;
		const width = container.clientWidth || container.getBoundingClientRect().width;
		const canvases = [];
		for (let number = 1; number <= Math.min(pdf.numPages, MAX_PAGES); number++) {
			const page = await pdf.getPage(number);
			const scale =
				(width / page.getViewport({ scale: 1 }).width) * (window.devicePixelRatio || 1);
			const viewport = page.getViewport({ scale });
			const canvas = document.createElement("canvas");
			canvas.width = Math.floor(viewport.width);
			canvas.height = Math.floor(viewport.height);
			await page.render({ canvas, viewport }).promise;
			canvases.push(canvas);
		}
		container.replaceChildren(...canvases);
		return { page_count: pdf.numPages };
	} finally {
		task.destroy();
	}
};
