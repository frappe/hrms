import { _ as m } from "./DateField-DafgtgxX.js";
import { o as u, d as o, g as f, J as c, a as i } from "./frappe-ui-D0k6koYp.js";
const p = {
	__name: "RequestField",
	props: {
		field: { type: Object, required: !0 },
		modelValue: { type: [String, Number, Boolean], default: "" },
	},
	emits: ["update:modelValue"],
	setup(e) {
		const a = e,
			r = i(
				() =>
					({
						number: "number",
						textarea: "textarea",
						select: "select",
						checkbox: "checkbox",
					})[a.field.type] || "text",
			),
			n = i(() => {
				if (a.field.type === "select")
					return [
						{ label: `Select a ${a.field.label.toLowerCase()}`, value: "" },
						...(a.field.options || []).map((l) => ({ label: l, value: l })),
					];
			});
		return (l, t) =>
			e.field.type === "date"
				? (u(),
				  o(
						m,
						{
							key: 0,
							"model-value": e.modelValue,
							label: e.field.label,
							required: e.field.required,
							"onUpdate:modelValue":
								t[0] || (t[0] = (d) => l.$emit("update:modelValue", d)),
						},
						null,
						8,
						["model-value", "label", "required"],
				  ))
				: (u(),
				  o(
						f(c),
						{
							key: 1,
							"model-value": e.modelValue,
							type: r.value,
							label: e.field.label,
							options: n.value,
							placeholder: e.field.placeholder,
							required: e.field.type === "checkbox" ? void 0 : e.field.required,
							"onUpdate:modelValue":
								t[1] || (t[1] = (d) => l.$emit("update:modelValue", d)),
						},
						null,
						8,
						["model-value", "type", "label", "options", "placeholder", "required"],
				  ));
	},
};
export { p as _ };
