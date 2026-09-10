import {
	o as t,
	h as s,
	f,
	g as d,
	y as g,
	k as b,
	X as o,
	e as c,
	d as m,
	al as y,
	z as i,
	t as r,
	a as x,
	s as u,
	I as k,
} from "./frappe-ui-D0k6koYp.js";
const p = { class: "mx-auto flex w-full max-w-[900px] flex-col gap-3.5 p-3 sm:p-4 lg:p-5" },
	$ = { key: 0, class: "flex items-center gap-2 py-6 text-base text-ink-gray-5" },
	j = {
		__name: "PageBody",
		props: { loading: Boolean },
		setup(e) {
			return (a, n) => (
				t(),
				s("div", p, [
					e.loading
						? (t(),
						  s("div", $, [
								f(d(g), { class: "h-4 w-4" }),
								n[0] || (n[0] = b(" Loading ", -1)),
						  ]))
						: o(a.$slots, "default", {}, void 0, void 0, 1),
				])
			);
		},
	},
	h = { class: "flex flex-wrap items-end justify-between gap-3" },
	_ = { class: "min-w-0" },
	v = { key: 1, class: "truncate text-2xl-semibold text-ink-gray-9" },
	w = { key: 2, class: "mt-0.5 text-base text-ink-gray-5" },
	S = { key: 0, class: "flex flex-wrap items-center gap-2" },
	z = {
		__name: "PageHead",
		props: { title: String, subtitle: String, crumbs: Array },
		setup(e) {
			const a = e,
				n = x(() => (a.crumbs || []).map((l) => ({ label: l.label, route: l.to })));
			return (l, N) => (
				t(),
				s("div", h, [
					c("div", _, [
						n.value.length
							? (t(),
							  m(d(y), { key: 0, class: "mb-0.5", items: n.value }, null, 8, [
									"items",
							  ]))
							: i("", !0),
						e.title ? (t(), s("h1", v, r(e.title), 1)) : i("", !0),
						e.subtitle ? (t(), s("p", w, r(e.subtitle), 1)) : i("", !0),
					]),
					l.$slots.actions ? (t(), s("div", S, [o(l.$slots, "actions")])) : i("", !0),
				])
			);
		},
	},
	B = { class: "text-base-semibold text-ink-gray-9" },
	C = { class: "shrink-0" },
	L = { key: 1, class: "text-base text-ink-gray-5" },
	P = {
		__name: "SectionCard",
		props: {
			title: String,
			action: String,
			readonlyLabel: String,
			padded: { type: Boolean, default: !0 },
		},
		emits: ["action"],
		setup(e) {
			return (a, n) => (
				t(),
				s(
					"section",
					{
						class: u([
							"flex flex-col rounded-6 border border-outline-gray-1 bg-surface-base",
							e.padded ? "gap-3 p-3.5" : "",
						]),
					},
					[
						e.title || a.$slots.action
							? (t(),
							  s(
									"header",
									{
										key: 0,
										class: u([
											"flex items-center justify-between gap-2",
											!e.padded && "px-3.5 pb-2.5 pt-3",
										]),
									},
									[
										c("h2", B, r(e.title), 1),
										c("div", C, [
											o(a.$slots, "action", {}, () => [
												e.action
													? (t(),
													  m(
															d(k),
															{
																key: 0,
																class: "-mr-2",
																variant: "ghost",
																label: e.action,
																onClick:
																	n[0] ||
																	(n[0] = (l) =>
																		a.$emit("action")),
															},
															null,
															8,
															["label"],
													  ))
													: e.readonlyLabel
													  ? (t(), s("span", L, r(e.readonlyLabel), 1))
													  : i("", !0),
											]),
										]),
									],
									2,
							  ))
							: i("", !0),
						o(a.$slots, "default"),
					],
					2,
				)
			);
		},
	};
export { P as _, z as a, j as b };
