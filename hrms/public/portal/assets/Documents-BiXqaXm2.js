import { a as b, _ as d, b as g } from "./SectionCard-BKeIA1B1.js";
import { _ as h } from "./DashGrid-CcXWxztj.js";
import { _ as u } from "./DataTable-KquPBl5L.js";
import { _ as v } from "./StatusBadge-DcMGXIA6.js";
import { v as l, d as c } from "./index-BpEXs0_U.js";
import {
	L as w,
	o as f,
	e as _,
	w as a,
	f as i,
	l as n,
	t as s,
	h as o,
	I as $,
	z as C,
	a as z,
} from "./frappe-ui-CXkWuvNK.js";
import "./EmptyState-DhAxAin0.js";
const O = {
	__name: "Documents",
	setup(D) {
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
			r = z(() => l.data);
		function k(e) {
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
			w(() => l.fetch()),
			(e, x) => (
				f(),
				_(
					g,
					{ loading: o(l).loading && !o(l).data },
					{
						default: a(() => [
							i(b, {
								title: "Documents",
								subtitle: "Company files and your own records",
							}),
							r.value
								? (f(),
								  _(
										h,
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
																	rows: r.value.company,
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
																				s(k(t.file_size)),
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
															i(o($), {
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
																	rows: r.value.mine,
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
export { O as default };
