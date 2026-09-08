import {
	b as D,
	P,
	o as v,
	f as w,
	g as l,
	h as e,
	s as N,
	F as B,
	k as i,
	i as u,
	M as C,
	B as m,
	x as _,
	C as S,
	a as y,
} from "./frappe-ui-BQ9PgXrr.js";
import { _ as d, a as M } from "./SectionCard-u_7VCKnT.js";
import { _ as F } from "./PageHead-3jtDpZ9g.js";
import { _ as R } from "./DashGrid-Bd23iLvt.js";
import { _ as V } from "./DataTable-vZ6Z-J3d.js";
import { _ as A } from "./StatTiles-YoNxs_Qn.js";
import { _ as b } from "./StatusBadge-Bqz4zlkD.js";
import { _ as n } from "./FieldRow-DbBPtAxY.js";
import { p as c, b as r, d as p } from "./index-DKSqIuAQ.js";
import "./EmptyState-DNwecFw5.js";
const E = { class: "font-semibold text-ink-gray-9" },
	I = { class: "flex flex-col" },
	G = { class: "flex flex-col" },
	O = { class: "flex flex-col" },
	W = {
		__name: "Payslips",
		setup(T) {
			const k = [
					{ key: "period", label: "Period", primary: !0 },
					{
						key: "gross_pay",
						label: "Gross",
						align: "right",
						nums: !0,
						muted: !0,
						hideOnMobile: !0,
					},
					{
						key: "total_deduction",
						label: "Deductions",
						align: "right",
						nums: !0,
						muted: !0,
						hideOnMobile: !0,
					},
					{ key: "net_pay", label: "Net Pay", align: "right", nums: !0 },
					{ key: "status", label: "Status", align: "right", badge: !0 },
				],
				h = D(),
				a = y(() => c.data),
				g = y(() => {
					var o;
					const s = ((o = a.value) == null ? void 0 : o.ytd) || {};
					return [
						{
							label: "Gross, Year to Date",
							value: r(s.gross, { compact: !0 }),
							hint: `${s.months || 0} months paid`,
						},
						{
							label: "Deductions",
							value: r(s.deductions, { compact: !0 }),
							hint: "tax, PF and other",
						},
						{
							label: "Net Paid",
							value: r(s.net, { compact: !0 }),
							hint: s.last_paid ? `last ${p(s.last_paid)}` : "",
						},
					];
				});
			function x(s) {
				h.push(`/payslips/${encodeURIComponent(s.name)}`);
			}
			function $(s) {
				window.location.href = `/app/${s}/new`;
			}
			return (
				P(() => c.fetch()),
				(s, o) => (
					v(),
					w(
						M,
						{ loading: u(c).loading && !u(c).data },
						{
							default: l(() => [
								e(F, { title: "Payslips", subtitle: "Your salary history" }),
								a.value
									? (v(),
									  N(
											B,
											{ key: 0 },
											[
												e(A, { tiles: g.value }, null, 8, ["tiles"]),
												e(R, null, {
													main: l(() => [
														e(
															d,
															{
																title: "Monthly Payslips",
																padded: !1,
															},
															{
																default: l(() => [
																	e(
																		V,
																		{
																			columns: k,
																			rows: a.value.slips,
																			clickable: "",
																			"empty-message":
																				"No payslips have been issued to you yet.",
																			onRowClick: x,
																		},
																		{
																			"cell-gross_pay": l(
																				({ row: t }) => [
																					m(
																						_(
																							u(r)(
																								t.gross_pay,
																							),
																						),
																						1,
																					),
																				],
																			),
																			"cell-total_deduction":
																				l(({ row: t }) => [
																					m(
																						_(
																							u(r)(
																								t.total_deduction,
																							),
																						),
																						1,
																					),
																				]),
																			"cell-net_pay": l(
																				({ row: t }) => [
																					i(
																						"span",
																						E,
																						_(
																							u(r)(
																								t.net_pay,
																							),
																						),
																						1,
																					),
																				],
																			),
																			"cell-status": l(
																				({ row: t }) => [
																					e(
																						b,
																						{
																							status:
																								t.docstatus ===
																								1
																									? t.status
																									: "Draft",
																						},
																						null,
																						8,
																						["status"],
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
													side: l(() => [
														e(
															d,
															{ title: "Tax Declaration" },
															{
																action: l(() => [
																	e(
																		b,
																		{
																			status: a.value.tax
																				.has_declaration
																				? "submitted"
																				: "due",
																			label: a.value.tax
																				.has_declaration
																				? "Submitted"
																				: "Not declared",
																		},
																		null,
																		8,
																		["status", "label"],
																	),
																]),
																default: l(() => [
																	i("dl", I, [
																		e(
																			n,
																			{
																				label: "Declared",
																				value: u(r)(
																					a.value.tax
																						.declared,
																				),
																				nums: "",
																			},
																			null,
																			8,
																			["value"],
																		),
																		e(
																			n,
																			{
																				label: "Period ends",
																				value: a.value.tax
																					.period_end
																					? u(p)(
																							a.value
																								.tax
																								.period_end,
																					  )
																					: "",
																				nums: "",
																			},
																			null,
																			8,
																			["value"],
																		),
																	]),
																	e(
																		u(C),
																		{
																			variant: "subtle",
																			class: "mt-1 w-full",
																			onClick:
																				o[0] ||
																				(o[0] = (t) =>
																					$(
																						"employee-tax-exemption-declaration",
																					)),
																		},
																		{
																			default: l(() => [
																				...(o[2] ||
																					(o[2] = [
																						m(
																							" Declare Investments ",
																							-1,
																						),
																					])),
																			]),
																			_: 1,
																		},
																	),
																]),
																_: 1,
															},
														),
														e(
															d,
															{
																title: "Salary Structure",
																"readonly-label": "HR-owned",
															},
															{
																default: l(() => {
																	var t, f;
																	return [
																		i("dl", G, [
																			e(
																				n,
																				{
																					label: "Structure",
																					value:
																						(t =
																							a.value
																								.structure) ==
																						null
																							? void 0
																							: t.salary_structure,
																					locked: "",
																				},
																				null,
																				8,
																				["value"],
																			),
																			e(
																				n,
																				{
																					label: "Effective",
																					value:
																						(f =
																							a.value
																								.structure) !=
																							null &&
																						f.from_date
																							? u(p)(
																									a
																										.value
																										.structure
																										.from_date,
																							  )
																							: "",
																					locked: "",
																					nums: "",
																				},
																				null,
																				8,
																				["value"],
																			),
																		]),
																	];
																}),
																_: 1,
															},
														),
														e(
															d,
															{
																title: "Bank Account",
																action: "Edit",
																onAction:
																	o[1] ||
																	(o[1] = (t) =>
																		s.$router.push("/me")),
															},
															{
																default: l(() => [
																	i("dl", O, [
																		e(
																			n,
																			{
																				label: "Bank",
																				value: a.value.bank
																					.bank_name,
																			},
																			null,
																			8,
																			["value"],
																		),
																		e(
																			n,
																			{
																				label: "Account",
																				value: a.value.bank
																					.account,
																				nums: "",
																			},
																			null,
																			8,
																			["value"],
																		),
																		e(
																			n,
																			{
																				label: "IFSC",
																				value: a.value.bank
																					.ifsc,
																			},
																			null,
																			8,
																			["value"],
																		),
																	]),
																]),
																_: 1,
															},
														),
													]),
													_: 1,
												}),
											],
											64,
									  ))
									: S("", !0),
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
export { W as default };
