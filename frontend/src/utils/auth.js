const HRMS_BASE_PATH = "/hrms"

export function buildHrmsPath(path = "/") {
	if (!path || path === "/") {
		return HRMS_BASE_PATH
	}

	if (path.startsWith(HRMS_BASE_PATH)) {
		return path
	}

	if (path.startsWith("/")) {
		return `${HRMS_BASE_PATH}${path}`
	}

	return `${HRMS_BASE_PATH}/${path}`
}

export function buildAmeideOidcLoginHref(
	path = window.location.pathname + window.location.search + window.location.hash,
) {
	const redirectTo = buildHrmsPath(path)
	return `/auth/ameide-oidc?redirect-to=${encodeURIComponent(redirectTo)}`
}

export function redirectToAmeideOidc(path) {
	window.location.assign(buildAmeideOidcLoginHref(path))
}

export function redirectToAmeideLogout() {
	window.location.assign("/auth/ameide-oidc/logout")
}
