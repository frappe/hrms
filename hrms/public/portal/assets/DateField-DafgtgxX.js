import {
	o as l,
	h as a,
	k as r,
	t as n,
	z as o,
	f as c,
	g as u,
	a3 as i,
} from "./frappe-ui-D0k6koYp.js";
const m = { class: "flex flex-col gap-1.5" },
	f = { key: 0, class: "block text-base text-ink-gray-5" },
	p = { key: 0, class: "text-ink-red-6" },
	V = {
		__name: "DateField",
		props: {
			modelValue: String,
			label: String,
			required: Boolean,
			placeholder: { type: String, default: "Select a date" },
		},
		emits: ["update:modelValue"],
		setup(e) {
			return (s, t) => (
				l(),
				a("div", m, [
					e.label
						? (l(),
						  a("label", f, [
								r(n(e.label) + " ", 1),
								e.required ? (l(), a("span", p, "*")) : o("", !0),
						  ]))
						: o("", !0),
					c(
						u(i),
						{
							class: "w-full",
							"input-class": "w-full",
							"model-value": e.modelValue,
							placeholder: e.placeholder,
							format: "D MMM YYYY",
							"onUpdate:modelValue":
								t[0] || (t[0] = (d) => s.$emit("update:modelValue", d)),
						},
						null,
						8,
						["model-value", "placeholder"],
					),
				])
			);
		},
	};
export { V as _ };
