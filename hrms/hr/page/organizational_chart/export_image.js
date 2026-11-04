// Saves the chart as a PNG. A page island cannot add an image library, so a copy of the chart
// goes into an SVG <foreignObject>, which is drawn onto a canvas.

// twice the pixels, for sharp text when zoomed
const SCALE = 2;
// browser canvas limits (Safari: ~16.7M pixels). A larger chart is drawn smaller.
const MAX_SIDE = 16000;
const MAX_PIXELS = 16_000_000;

export async function export_image(element, file_name) {
	const width = element.offsetWidth;
	const height = element.offsetHeight;
	const scale = Math.min(
		SCALE,
		MAX_SIDE / width,
		MAX_SIDE / height,
		Math.sqrt(MAX_PIXELS / (width * height)),
	);

	const copy = element.cloneNode(true);
	// full size, without the canvas's pan and zoom
	copy.style.transform = "none";
	copy.style.position = "static";
	await inline_photos(copy);

	const wrapper = document.createElement("div");
	wrapper.setAttribute("xmlns", "http://www.w3.org/1999/xhtml");
	// design tokens and text styles come from the island root, which the copy is outside of
	wrapper.setAttribute("style", inherited_styles(element));
	const style = document.createElement("style");
	style.textContent = (await font_faces(element)) + stylesheet_text(element.getRootNode());
	wrapper.append(style, copy);

	const svg =
		`<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}">` +
		`<foreignObject width="100%" height="100%">${new XMLSerializer().serializeToString(
			wrapper,
		)}</foreignObject></svg>`;

	const image = new Image();
	image.src = `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
	await image.decode();

	const canvas = document.createElement("canvas");
	canvas.width = Math.ceil(width * scale);
	canvas.height = Math.ceil(height * scale);
	const context = canvas.getContext("2d");
	context.fillStyle = getComputedStyle(element.parentElement).backgroundColor;
	context.fillRect(0, 0, canvas.width, canvas.height);
	context.scale(scale, scale);
	context.drawImage(image, 0, 0);

	const blob = await new Promise((resolve) => canvas.toBlob(resolve, "image/png"));
	if (!blob) throw new Error("The browser could not draw a canvas of this size");
	const link = document.createElement("a");
	link.href = URL.createObjectURL(blob);
	link.download = `${file_name}.png`;
	link.click();
	URL.revokeObjectURL(link.href);
}

// the island's styles live on its shadow root, not in the page
function stylesheet_text(root) {
	const sheets = [...(root.adoptedStyleSheets || []), ...root.querySelectorAll("style")];
	return sheets
		.flatMap((sheet) => {
			if (sheet instanceof HTMLStyleElement) return [sheet.textContent];
			return [...sheet.cssRules].map((rule) => rule.cssText);
		})
		.join("\n");
}

// An SVG drawn as an image loads no fonts, so the chart's font goes in as data. Fetched once,
// and again after a failure.
let font_css = "";

async function font_faces(element) {
	if (font_css) return font_css;

	const family = getComputedStyle(element).fontFamily.split(",")[0].trim().replace(/["']/g, "");
	const faces = [];
	for (const sheet of [
		...document.styleSheets,
		...(element.getRootNode().adoptedStyleSheets || []),
	]) {
		let rules;
		try {
			rules = sheet.cssRules;
		} catch {
			// a stylesheet from another origin cannot be read
			continue;
		}
		for (const rule of rules) {
			if (!(rule instanceof CSSFontFaceRule)) continue;
			if (rule.style.getPropertyValue("font-family").replace(/["']/g, "") !== family)
				continue;
			if (rule.style.getPropertyValue("font-style") === "italic") continue;
			faces.push(embed_font_face(rule, sheet.href || document.baseURI));
		}
	}

	font_css = (await Promise.all(faces)).join("\n");
	return font_css;
}

async function embed_font_face(rule, base) {
	const url = rule.style.getPropertyValue("src").match(/url\(["']?([^"')]+)["']?\)/)?.[1];
	if (!url) return "";
	try {
		const response = await fetch(new URL(url, base));
		const data_url = await as_data_url(await response.blob());
		return rule.cssText.replace(/src:[^;]+;/, `src: url("${data_url}");`);
	} catch {
		// the image falls back to the default face
		return "";
	}
}

const INHERITED_TEXT_STYLES = [
	"font-family",
	"font-size",
	"line-height",
	"color",
	"letter-spacing",
];

function inherited_styles(element) {
	const computed = getComputedStyle(element);
	return [...computed]
		.filter((name) => name.startsWith("--"))
		.concat(INHERITED_TEXT_STYLES)
		.map((name) => `${name}:${computed.getPropertyValue(name)}`)
		.join(";");
}

// An SVG drawn as an image loads nothing, so photos go in as data. A photo on another site would
// fail CORS, so it becomes the person's initial, as an avatar without a photo does.
async function inline_photos(copy) {
	await Promise.all(
		[...copy.querySelectorAll("img")].map(async (img) => {
			try {
				if (new URL(img.src).origin !== location.origin)
					throw new Error("photo on another site");
				const response = await fetch(img.src);
				if (!response.ok) throw new Error(response.statusText);
				img.src = await as_data_url(await response.blob());
				img.removeAttribute("srcset");
			} catch {
				const initial = document.createElement("span");
				initial.className =
					"flex h-full w-full items-center justify-center rounded-full bg-surface-gray-2 text-ink-gray-5";
				initial.textContent = (img.alt || "?").trim().charAt(0).toUpperCase();
				img.replaceWith(initial);
			}
		}),
	);
}

function as_data_url(blob) {
	return new Promise((resolve, reject) => {
		const reader = new FileReader();
		reader.onload = () => resolve(reader.result);
		reader.onerror = reject;
		reader.readAsDataURL(blob);
	});
}
