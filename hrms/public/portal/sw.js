if (!self.define) {
	let s,
		e = {};
	const l = (l, i) => (
		(l = new URL(l + ".js", i).href),
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
	self.define = (i, n) => {
		const r = s || ("document" in self ? document.currentScript.src : "") || location.href;
		if (e[r]) return;
		let u = {};
		const t = (s) => l(s, r),
			a = { module: { uri: r }, exports: u, require: t };
		e[r] = Promise.all(i.map((s) => a[s] || t(s))).then((s) => (n(...s), u));
	};
}
define(["./workbox-0bb07689"], function (s) {
	"use strict";
	self.skipWaiting(),
		s.clientsClaim(),
		s.precacheAndRoute(
			[
				{ url: "registerSW.js", revision: "7519ffe4bee5819351778bc0b11a9342" },
				{ url: "index.html", revision: "a2aa235d20e217b4b4d9a05466351113" },
				{ url: "assets/toast-BPVivXt-.js", revision: null },
				{ url: "assets/index-BSaIzYPn.js", revision: null },
				{ url: "assets/index-BDq9BcFq.css", revision: null },
				{ url: "assets/frappe-ui-Gd3P3Yvw.css", revision: null },
				{ url: "assets/frappe-ui-D0k6koYp.js", revision: null },
				{ url: "assets/TotalRow-DhNOuPhk.js", revision: null },
				{ url: "assets/StatusBadge-sSVuNJEI.js", revision: null },
				{ url: "assets/StatTiles-CcQndbp7.js", revision: null },
				{ url: "assets/SectionCard-C5Qs8pBJ.js", revision: null },
				{ url: "assets/RequestField-CEA0aLLd.js", revision: null },
				{ url: "assets/RequestDialog-UMsP4D4j.js", revision: null },
				{ url: "assets/Request-hIkiCd30.js", revision: null },
				{ url: "assets/Profile-DYVnOsur.js", revision: null },
				{ url: "assets/PersonRow-2k8WhDWN.js", revision: null },
				{ url: "assets/Payslips-BO4rJX6X.js", revision: null },
				{ url: "assets/Payslip-_l5-BTWq.js", revision: null },
				{ url: "assets/OrgChart-C1AHL9m-.js", revision: null },
				{ url: "assets/Leave-ByXBDfov.js", revision: null },
				{ url: "assets/Inter.var-C9xDBOS3.woff2", revision: null },
				{ url: "assets/Inter-Italic.var-BGHziHgI.woff2", revision: null },
				{ url: "assets/IdentityBand-BZ37_HBf.js", revision: null },
				{ url: "assets/Home-C0pHjBgn.js", revision: null },
				{ url: "assets/Holidays-DQnJRsKu.js", revision: null },
				{ url: "assets/FieldRow-DoxIhPye.js", revision: null },
				{ url: "assets/Extension-Dw3zvxtZ.js", revision: null },
				{ url: "assets/Expenses-suXsNGZy.js", revision: null },
				{ url: "assets/EmptyState-38_uLDf3.js", revision: null },
				{ url: "assets/Documents-DN62iRzA.js", revision: null },
				{ url: "assets/Directory-CCxFXTcR.js", revision: null },
				{ url: "assets/DateField-DafgtgxX.js", revision: null },
				{ url: "assets/DataTable-BPI_hH2T.js", revision: null },
				{ url: "assets/DataTable-BCMkhabB.css", revision: null },
				{ url: "assets/DashGrid-CGnJY6QD.js", revision: null },
				{ url: "assets/Colleague-CqZ7kh9t.js", revision: null },
				{ url: "assets/BalanceBars-9ROF_iIl.js", revision: null },
				{ url: "assets/Attendance-DsdvaukV.js", revision: null },
				{ url: "assets/Advances-tyJB2sdK.js", revision: null },
				{ url: "manifest.webmanifest", revision: "8357eaf9ca5c75638afd6bf63f8500f1" },
			],
			{},
		),
		s.cleanupOutdatedCaches();
});
