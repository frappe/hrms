import { a4 as r } from "./frappe-ui-D0k6koYp.js";
function a(n, o) {
	r.success(s(n, o));
}
function i(n, o) {
	r.error(s(n, o));
}
function u(n, o) {
	r.info(s(n, o));
}
function s(n, o) {
	return o ? `${n}. ${o}` : n;
}
function c(n, o) {
	var t;
	return (
		((t = n == null ? void 0 : n.messages) == null ? void 0 : t[0]) ||
		(n == null ? void 0 : n.message) ||
		o
	);
}
export { i as a, u as b, c as e, a as n };
