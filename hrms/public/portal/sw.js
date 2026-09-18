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
				{ url: "index.html", revision: "8701eb402d861d6ef2486f6f4da56c73" },
				{ url: "assets/toast-Ca-cKV9o.js", revision: null },
				{ url: "assets/index-DhuFHe0B.css", revision: null },
				{ url: "assets/index-BpEXs0_U.js", revision: null },
				{ url: "assets/frappe-ui-Gd3P3Yvw.css", revision: null },
				{ url: "assets/frappe-ui-CXkWuvNK.js", revision: null },
				{ url: "assets/TotalRow-CVxIYHPR.js", revision: null },
				{ url: "assets/StatusBadge-DcMGXIA6.js", revision: null },
				{ url: "assets/StatTiles-knaJnTjR.js", revision: null },
				{ url: "assets/SectionCard-BKeIA1B1.js", revision: null },
				{ url: "assets/Score-Dz0zaDXE.js", revision: null },
				{ url: "assets/RequestField-B8HqhQXt.js", revision: null },
				{ url: "assets/RequestDialog-DuFWjain.js", revision: null },
				{ url: "assets/Request-DoyYVLTK.js", revision: null },
				{ url: "assets/Profile-D_m9OkBn.js", revision: null },
				{ url: "assets/PersonRow-BtXbdUjH.js", revision: null },
				{ url: "assets/Payslips-F3aI3vOI.js", revision: null },
				{ url: "assets/Payslip-BFdUwNvP.js", revision: null },
				{ url: "assets/OrgChart-ajZIQDO0.js", revision: null },
				{ url: "assets/Leave-ChQtt7Lk.js", revision: null },
				{ url: "assets/Inter.var-C9xDBOS3.woff2", revision: null },
				{ url: "assets/Inter-Italic.var-BGHziHgI.woff2", revision: null },
				{ url: "assets/IdentityBand-DFaFZaDc.js", revision: null },
				{ url: "assets/Home-BlUsb_74.js", revision: null },
				{ url: "assets/Holidays-BDD9rzGz.js", revision: null },
				{ url: "assets/FieldRow-2cmCHPuL.js", revision: null },
				{ url: "assets/Extension-CSwDbGjD.js", revision: null },
				{ url: "assets/Expenses-CQTc1zQ3.js", revision: null },
				{ url: "assets/EmptyState-DhAxAin0.js", revision: null },
				{ url: "assets/Documents-BiXqaXm2.js", revision: null },
				{ url: "assets/Directory-Cjc6dUR2.js", revision: null },
				{ url: "assets/DateField-BLUeL_2-.js", revision: null },
				{ url: "assets/DataTable-KquPBl5L.js", revision: null },
				{ url: "assets/DataTable-BCMkhabB.css", revision: null },
				{ url: "assets/DashGrid-CcXWxztj.js", revision: null },
				{ url: "assets/Colleague-BqZPReOK.js", revision: null },
				{ url: "assets/Attendance-BQn40tyw.js", revision: null },
				{ url: "assets/Appraisals-CSn8NeWg.js", revision: null },
				{ url: "assets/Appraisal-BhPEP4AC.js", revision: null },
				{ url: "assets/Advances-C1gOEb44.js", revision: null },
				{ url: "manifest.webmanifest", revision: "8357eaf9ca5c75638afd6bf63f8500f1" },
			],
			{},
		),
		s.cleanupOutdatedCaches();
});
