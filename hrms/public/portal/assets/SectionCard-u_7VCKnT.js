import {
	o as t,
	s as n,
	h as f,
	i as c,
	A as u,
	B as m,
	a2 as l,
	v as o,
	k as i,
	x as d,
	f as g,
	M as x,
	C as r,
} from "./frappe-ui-BQ9PgXrr.js";
const y = { class: "mx-auto flex w-full max-w-[1440px] flex-col gap-3.5 p-3 sm:p-4 lg:p-5" },
	b = { key: 0, class: "flex items-center gap-2 py-6 text-base text-ink-gray-5" },
	v = {
		__name: "PageBody",
		props: { loading: Boolean },
		setup(e) {
			return (a, s) => (
				t(),
				n("div", y, [
					e.loading
						? (t(),
						  n("div", b, [
								f(c(u), { class: "h-4 w-4" }),
								s[0] || (s[0] = m(" Loading ", -1)),
						  ]))
						: l(a.$slots, "default", {}, void 0, void 0, 1),
				])
			);
		},
	},
	p = { class: "text-base font-semibold text-ink-gray-9" },
	k = { class: "shrink-0" },
	$ = { key: 1, class: "text-base text-ink-gray-5" },
	S = {
		__name: "SectionCard",
		props: {
			title: String,
			action: String,
			readonlyLabel: String,
			padded: { type: Boolean, default: !0 },
		},
		emits: ["action"],
		setup(e) {
			return (a, s) => (
				t(),
				n(
					"section",
					{
						class: o([
							"flex flex-col rounded-lg border border-outline-gray-1 bg-surface-white",
							e.padded ? "gap-3 p-3.5" : "",
						]),
					},
					[
						e.title || a.$slots.action
							? (t(),
							  n(
									"header",
									{
										key: 0,
										class: o([
											"flex items-center justify-between gap-2",
											!e.padded && "px-3.5 pb-2.5 pt-3",
										]),
									},
									[
										i("h2", p, d(e.title), 1),
										i("div", k, [
											l(a.$slots, "action", {}, () => [
												e.action
													? (t(),
													  g(
															c(x),
															{
																key: 0,
																class: "-mr-2",
																variant: "ghost",
																label: e.action,
																onClick:
																	s[0] ||
																	(s[0] = (h) =>
																		a.$emit("action")),
															},
															null,
															8,
															["label"],
													  ))
													: e.readonlyLabel
													  ? (t(), n("span", $, d(e.readonlyLabel), 1))
													  : r("", !0),
											]),
										]),
									],
									2,
							  ))
							: r("", !0),
						l(a.$slots, "default"),
					],
					2,
				)
			);
		},
	};
export { S as _, v as a };
