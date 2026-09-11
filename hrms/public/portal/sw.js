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
	self.define = (i, r) => {
		const n = s || ("document" in self ? document.currentScript.src : "") || location.href;
		if (e[n]) return;
		let u = {};
		const t = (s) => l(s, n),
			a = { module: { uri: n }, exports: u, require: t };
		e[n] = Promise.all(i.map((s) => a[s] || t(s))).then((s) => (r(...s), u));
	};
}
define(["./workbox-0bb07689"], function (s) {
	"use strict";
	self.skipWaiting(),
		s.clientsClaim(),
		s.precacheAndRoute(
			[
				{ url: "registerSW.js", revision: "7519ffe4bee5819351778bc0b11a9342" },
				{ url: "index.html", revision: "a5446eb668e2a42057e1c6855bcf2e7c" },
				{ url: "assets/toast-BxUFHbEO.js", revision: null },
				{ url: "assets/index-B--0C4K1.css", revision: null },
				{ url: "assets/index-6wvshjQq.js", revision: null },
				{ url: "assets/frappe-ui-rHlwnvVy.js", revision: null },
				{ url: "assets/frappe-ui-Gd3P3Yvw.css", revision: null },
				{ url: "assets/TotalRow-DkNHj82l.js", revision: null },
				{ url: "assets/StatusBadge-ZWn2FvVw.js", revision: null },
				{ url: "assets/StatTiles-DcUJsMoQ.js", revision: null },
				{ url: "assets/SectionCard-0tgyDAFI.js", revision: null },
				{ url: "assets/Score-BvtjKy2-.js", revision: null },
				{ url: "assets/RequestField-DnRQOkWG.js", revision: null },
				{ url: "assets/RequestDialog-CkjqgI3z.js", revision: null },
				{ url: "assets/Request-BCiea5PY.js", revision: null },
				{ url: "assets/Profile-D58gBTjj.js", revision: null },
				{ url: "assets/PersonRow-LB2-2vnj.js", revision: null },
				{ url: "assets/Payslips-B67ljCeC.js", revision: null },
				{ url: "assets/Payslip-Bvm3Puua.js", revision: null },
				{ url: "assets/OrgChart-BDXM5PiR.js", revision: null },
				{ url: "assets/Leave-zKj4hB5t.js", revision: null },
				{ url: "assets/Inter.var-C9xDBOS3.woff2", revision: null },
				{ url: "assets/Inter-Italic.var-BGHziHgI.woff2", revision: null },
				{ url: "assets/IdentityBand-BrhYzFba.js", revision: null },
				{ url: "assets/Home-CZEAq-8Z.js", revision: null },
				{ url: "assets/Holidays-CdZzNhou.js", revision: null },
				{ url: "assets/FieldRow-C13lI4HG.js", revision: null },
				{ url: "assets/Extension-k16Q2tGz.js", revision: null },
				{ url: "assets/Expenses-VluYc6Cc.js", revision: null },
				{ url: "assets/EmptyState-0_BFjfJU.js", revision: null },
				{ url: "assets/Documents-ZAuSBXm4.js", revision: null },
				{ url: "assets/Directory-C908hIDk.js", revision: null },
				{ url: "assets/DateField-c9rL8vfk.js", revision: null },
				{ url: "assets/DataTable-BY05XQx8.js", revision: null },
				{ url: "assets/DataTable-BCMkhabB.css", revision: null },
				{ url: "assets/DashGrid-Cmnm2mAO.js", revision: null },
				{ url: "assets/Colleague-aNRW7q3S.js", revision: null },
				{ url: "assets/Attendance-D3Lf9b9X.js", revision: null },
				{ url: "assets/Appraisals-F_9rEdQB.js", revision: null },
				{ url: "assets/Appraisal-C2-LaO9r.js", revision: null },
				{ url: "assets/Advances-BmsHPSTn.js", revision: null },
				{ url: "manifest.webmanifest", revision: "8357eaf9ca5c75638afd6bf63f8500f1" },
			],
			{},
		),
		s.cleanupOutdatedCaches();
});
