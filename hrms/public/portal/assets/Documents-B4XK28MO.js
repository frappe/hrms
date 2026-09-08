import { _ as d, a as k } from "./SectionCard-u_7VCKnT.js";
import { _ as h } from "./PageHead-3jtDpZ9g.js";
import { _ as b } from "./DashGrid-Bd23iLvt.js";
import { _ as u } from "./DataTable-vZ6Z-J3d.js";
import { _ as v } from "./StatusBadge-Bqz4zlkD.js";
import { r, d as c } from "./index-DKSqIuAQ.js";
import {
	P as $,
	o as f,
	f as _,
	g as a,
	h as i,
	B as n,
	x as s,
	i as o,
	M as w,
	C,
	a as x,
} from "./frappe-ui-BQ9PgXrr.js";
import "./EmptyState-DNwecFw5.js";
const R = {
	__name: "Documents",
	setup(B) {
		const p = [
				{ key: "file_name", label: "Document", primary: !0 },
				{ key: "file_size", label: "Size", nums: !0, muted: !0, hideOnMobile: !0 },
				{ key: "modified", label: "Updated", nums: !0, muted: !0, align: "right" },
			],
			y = [
				{ key: "file_name", label: "File", primary: !0 },
				{ key: "modified", label: "Added", nums: !0, muted: !0 },
				{ key: "is_private", label: "", align: "right", badge: !0 },
			],
			l = x(() => r.data);
		function g(e) {
			return e
				? e < 1024
					? `${e} B`
					: e < 1024 * 1024
					  ? `${Math.round(e / 1024)} KB`
					  : `${(e / 1024 / 1024).toFixed(1)} MB`
				: "—";
		}
		function m(e) {
			e.file_url && window.open(e.file_url, "_blank", "noopener");
		}
		return (
			$(() => r.fetch()),
			(e, D) => (
				f(),
				_(
					k,
					{ loading: o(r).loading && !o(r).data },
					{
						default: a(() => [
							i(h, {
								title: "Documents",
								subtitle: "Company files and your own records",
							}),
							l.value
								? (f(),
								  _(
										b,
										{ key: 0, ratio: "even" },
										{
											main: a(() => [
												i(
													d,
													{ title: "Company Documents", padded: !1 },
													{
														default: a(() => [
															i(
																u,
																{
																	columns: p,
																	rows: l.value.company,
																	clickable: "",
																	"empty-message":
																		"No company-wide documents have been shared yet.",
																	onRowClick: m,
																},
																{
																	"cell-modified": a(
																		({ row: t }) => [
																			n(
																				s(
																					o(c)(
																						t.modified,
																					),
																				),
																				1,
																			),
																		],
																	),
																	"cell-file_size": a(
																		({ row: t }) => [
																			n(
																				s(g(t.file_size)),
																				1,
																			),
																		],
																	),
																	_: 1,
																},
																8,
																["rows"],
															),
														]),
														_: 1,
													},
												),
											]),
											side: a(() => [
												i(
													d,
													{ title: "Issued to You", padded: !1 },
													{
														action: a(() => [
															i(o(w), {
																variant: "ghost",
																route: "/me",
																label: "Open Profile",
															}),
														]),
														default: a(() => [
															i(
																u,
																{
																	columns: y,
																	rows: l.value.mine,
																	clickable: "",
																	"empty-message":
																		"No documents are attached to your employee record.",
																	onRowClick: m,
																},
																{
																	"cell-modified": a(
																		({ row: t }) => [
																			n(
																				s(
																					o(c)(
																						t.modified,
																					),
																				),
																				1,
																			),
																		],
																	),
																	"cell-is_private": a(
																		({ row: t }) => [
																			i(
																				v,
																				{
																					status: t.is_private
																						? "gray"
																						: "available",
																					label: t.is_private
																						? "Private"
																						: "Shared",
																				},
																				null,
																				8,
																				[
																					"status",
																					"label",
																				],
																			),
																		],
																	),
																	_: 1,
																},
																8,
																["rows"],
															),
														]),
														_: 1,
													},
												),
											]),
											_: 1,
										},
								  ))
								: C("", !0),
						]),
						_: 1,
					},
					8,
					["loading"],
				)
			)
		);
	},
};
export { R as default };
