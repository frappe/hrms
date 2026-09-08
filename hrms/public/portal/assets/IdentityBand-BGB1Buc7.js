import { _ as g } from "./StatusBadge-Bqz4zlkD.js";
import {
	o as t,
	s as a,
	k as r,
	h as u,
	i as b,
	j as x,
	x as l,
	F as c,
	t as m,
	f,
	C as n,
	a2 as y,
} from "./frappe-ui-BQ9PgXrr.js";
const h = { class: "rounded-lg border border-outline-gray-1 bg-surface-white" },
	_ = { class: "flex flex-wrap items-start gap-4 p-4" },
	k = { class: "min-w-0 flex-1" },
	v = { class: "truncate text-lg font-semibold text-ink-gray-9 sm:text-xl" },
	w = { class: "mt-0.5 truncate text-p-base text-ink-gray-5" },
	p = { key: 0, class: "mt-2 flex flex-wrap gap-1.5" },
	B = { key: 0, class: "flex w-full flex-wrap gap-2 sm:w-auto" },
	S = {
		key: 0,
		class: "grid grid-cols-2 border-t border-outline-gray-1 sm:grid-cols-3 lg:grid-cols-5",
	},
	$ = { class: "nums truncate text-base font-semibold text-ink-gray-9" },
	N = { class: "mt-px truncate text-base text-ink-gray-5" },
	F = {
		__name: "IdentityBand",
		props: { name: String, image: String, meta: String, badges: Array, facts: Array },
		setup(e) {
			return (o, V) => {
				var i, d;
				return (
					t(),
					a("div", h, [
						r("div", _, [
							u(b(x), { label: e.name, image: e.image, size: "3xl" }, null, 8, [
								"label",
								"image",
							]),
							r("div", k, [
								r("h1", v, l(e.name), 1),
								r("p", w, l(e.meta), 1),
								(i = e.badges) != null && i.length
									? (t(),
									  a("div", p, [
											(t(!0),
											a(
												c,
												null,
												m(
													e.badges,
													(s) => (
														t(),
														f(
															g,
															{
																key: s.label,
																status: s.tone,
																label: s.label,
															},
															null,
															8,
															["status", "label"],
														)
													),
												),
												128,
											)),
									  ]))
									: n("", !0),
							]),
							o.$slots.actions
								? (t(), a("div", B, [y(o.$slots, "actions")]))
								: n("", !0),
						]),
						(d = e.facts) != null && d.length
							? (t(),
							  a("dl", S, [
									(t(!0),
									a(
										c,
										null,
										m(
											e.facts,
											(s) => (
												t(),
												a(
													"div",
													{
														key: s.label,
														class: "border-b border-r border-outline-gray-1 px-4 py-2 last:border-r-0 sm:border-b-0",
													},
													[
														r("dd", $, l(s.value || "—"), 1),
														r("dt", N, l(s.label), 1),
													],
												)
											),
										),
										128,
									)),
							  ]))
							: n("", !0),
					])
				);
			};
		},
	};
export { F as _ };
