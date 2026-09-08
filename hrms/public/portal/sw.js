if (!self.define) {
	let s,
		e = {};
	const l = (l, r) => (
		(l = new URL(l + ".js", r).href),
		e[l] ||
			new Promise((e) => {
				if ("document" in self) {
					const s = document.createElement("script");
					(s.src = l), (s.onload = e), document.head.appendChild(s);
				} else (s = l), importScripts(l), e();
			}).then(() => {
				let s = e[l];
				if (!s) throw new Error(`Module ${l} didn’t register its module`);
				return s;
			})
	);
	self.define = (r, i) => {
		const n = s || ("document" in self ? document.currentScript.src : "") || location.href;
		if (e[n]) return;
		let u = {};
		const t = (s) => l(s, n),
			o = { module: { uri: n }, exports: u, require: t };
		e[n] = Promise.all(r.map((s) => o[s] || t(s))).then((s) => (i(...s), u));
	};
}
define(["./workbox-0bb07689"], function (s) {
	"use strict";
	self.skipWaiting(),
		s.clientsClaim(),
		s.precacheAndRoute(
			[
				{ url: "registerSW.js", revision: "7519ffe4bee5819351778bc0b11a9342" },
				{ url: "index.html", revision: "dccd43c81915e0e609ecdc14f1fe277d" },
				{ url: "assets/toast-9qekBDJT.js", revision: null },
				{ url: "assets/index-DKSqIuAQ.js", revision: null },
				{ url: "assets/index-BWm--ni7.css", revision: null },
				{ url: "assets/frappe-ui-Bp8pEQrW.css", revision: null },
				{ url: "assets/frappe-ui-BQ9PgXrr.js", revision: null },
				{ url: "assets/StatusBadge-Bqz4zlkD.js", revision: null },
				{ url: "assets/StatTiles-YoNxs_Qn.js", revision: null },
				{ url: "assets/SectionCard-u_7VCKnT.js", revision: null },
				{ url: "assets/RequestDialog-TPB8mqrQ.js", revision: null },
				{ url: "assets/Request-B1_U03dg.js", revision: null },
				{ url: "assets/Profile-5WmgxzRt.js", revision: null },
				{ url: "assets/PersonRow-DZ4YBxpS.js", revision: null },
				{ url: "assets/Payslips-BPdeU3Bp.js", revision: null },
				{ url: "assets/Payslip-CFlv2Jvw.js", revision: null },
				{ url: "assets/PageHead-3jtDpZ9g.js", revision: null },
				{ url: "assets/OrgChart-CRKf-07x.css", revision: null },
				{ url: "assets/OrgChart-B5HV4bG-.js", revision: null },
				{ url: "assets/Leave-59X_GT51.js", revision: null },
				{ url: "assets/Inter.var-C9xDBOS3.woff2", revision: null },
				{ url: "assets/Inter-Italic.var-BGHziHgI.woff2", revision: null },
				{ url: "assets/IdentityBand-BGB1Buc7.js", revision: null },
				{ url: "assets/Home-DBGqMnyY.js", revision: null },
				{ url: "assets/Holidays-Bk9m_VhS.js", revision: null },
				{ url: "assets/FieldRow-DbBPtAxY.js", revision: null },
				{ url: "assets/Expenses-C-UGZDUr.js", revision: null },
				{ url: "assets/EmptyState-DNwecFw5.js", revision: null },
				{ url: "assets/Documents-B4XK28MO.js", revision: null },
				{ url: "assets/Directory-CbMhGYpC.js", revision: null },
				{ url: "assets/DataTable-vZ6Z-J3d.js", revision: null },
				{ url: "assets/DashGrid-Bd23iLvt.js", revision: null },
				{ url: "assets/Colleague-CM8SqR9s.js", revision: null },
				{ url: "assets/BalanceBars-CBgUe-mJ.js", revision: null },
				{ url: "assets/Attendance-CLV1kRNW.js", revision: null },
				{ url: "assets/Advances-D4z4VXmc.js", revision: null },
				{ url: "manifest.webmanifest", revision: "8357eaf9ca5c75638afd6bf63f8500f1" },
			],
			{},
		),
		s.cleanupOutdatedCaches();
});
