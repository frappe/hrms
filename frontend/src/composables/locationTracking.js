// Live location tracking.
//
// - Inside the native APK (Capacitor): uses the @capacitor-community/background-geolocation
//   plugin so tracking continues when the app is backgrounded / the screen is off.
// - In a plain browser / PWA: falls back to navigator.geolocation.watchPosition
//   (foreground only).
//
// Pings are buffered and flushed to the backend in batches via hr_app.api.log_locations.
// A localStorage queue makes pings survive connectivity drops and app restarts.

import { reactive } from "vue"
import { frappeRequest } from "frappe-ui"
import { Capacitor, registerPlugin } from "@capacitor/core"

const QUEUE_KEY = "hortiapp_location_queue"
const CONSENT_KEY = "hortiapp_tracking_consent"
const DEFAULT_INTERVAL = 60 // seconds

const CONSENT_MESSAGE =
	"While you are checked in, HortiApp records your location so your team can " +
	"coordinate field work. Tracking stops automatically when you check out. " +
	"Do you consent to location tracking during your shift?"

// One-time disclosure / consent. The OS permission dialog (native) is the real
// gate; this is the in-app disclosure required for background location.
function ensureConsent() {
	if (localStorage.getItem(CONSENT_KEY) === "granted") return true
	// window.confirm is available in both browsers and the Capacitor webview.
	const granted = typeof window !== "undefined" && window.confirm(CONSENT_MESSAGE)
	if (granted) localStorage.setItem(CONSENT_KEY, "granted")
	return granted
}

// Lazily registered native plugin proxy (no-op on web).
let BackgroundGeolocation = null
function getBackgroundGeolocation() {
	if (!BackgroundGeolocation) {
		BackgroundGeolocation = registerPlugin("BackgroundGeolocation")
	}
	return BackgroundGeolocation
}

// Module-level singleton state so tracking is global across the app.
export const trackingState = reactive({
	active: false,
})

let buffer = []
let flushTimer = null
let intervalSeconds = DEFAULT_INTERVAL
let webWatchId = null
let nativeWatcherId = null
let isNative = false

function loadQueue() {
	try {
		return JSON.parse(localStorage.getItem(QUEUE_KEY)) || []
	} catch {
		return []
	}
}

function saveQueue(pings) {
	try {
		localStorage.setItem(QUEUE_KEY, JSON.stringify(pings))
	} catch {
		// storage full / unavailable - drop silently
	}
}

function enqueue(ping) {
	if (!ping || ping.latitude == null || ping.longitude == null) return
	buffer.push(ping)
}

async function flush() {
	// Combine anything persisted from previous failed flushes with the live buffer.
	const pending = [...loadQueue(), ...buffer]
	buffer = []
	if (!pending.length) {
		saveQueue([])
		return
	}

	try {
		await frappeRequest({
			url: "hr_app.api.log_locations",
			method: "POST",
			params: { pings: JSON.stringify(pending) },
		})
		saveQueue([])
	} catch (err) {
		// keep the pings for the next attempt
		console.error("Failed to flush location pings:", err)
		saveQueue(pending)
	}
}

function startFlushTimer() {
	stopFlushTimer()
	flushTimer = setInterval(flush, intervalSeconds * 1000)
}

function stopFlushTimer() {
	if (flushTimer) {
		clearInterval(flushTimer)
		flushTimer = null
	}
}

async function startNative() {
	const plugin = getBackgroundGeolocation()
	nativeWatcherId = await plugin.addWatcher(
		{
			backgroundMessage: "Location is being tracked while you are checked in.",
			backgroundTitle: "HortiApp tracking active",
			requestPermissions: true,
			stale: false,
			distanceFilter: 10,
		},
		(location, error) => {
			if (error) {
				console.error("Background geolocation error:", error)
				return
			}
			if (!location) return
			enqueue({
				timestamp: new Date(location.time || Date.now()).toISOString(),
				latitude: location.latitude,
				longitude: location.longitude,
				accuracy: location.accuracy,
				speed: location.speed,
				source: "Background",
			})
		}
	)
}

function startWeb() {
	if (!navigator.geolocation) {
		console.error("Geolocation not supported in this browser")
		return
	}
	let lastCapture = 0
	webWatchId = navigator.geolocation.watchPosition(
		(pos) => {
			// throttle to roughly one ping per interval
			const now = Date.now()
			if (now - lastCapture < intervalSeconds * 1000) return
			lastCapture = now
			enqueue({
				timestamp: new Date(now).toISOString(),
				latitude: pos.coords.latitude,
				longitude: pos.coords.longitude,
				accuracy: pos.coords.accuracy,
				speed: pos.coords.speed,
				source: "Foreground",
			})
		},
		(err) => console.error("Geolocation watch error:", err),
		{ enableHighAccuracy: true, maximumAge: 0, timeout: 30000 }
	)
}

/**
 * Start location tracking.
 * @param {object} settings - HR settings ({ enable_live_tracking, tracking_interval })
 */
export async function startTracking(settings = {}) {
	if (trackingState.active) return
	if (!settings.enable_live_tracking) return
	if (!ensureConsent()) return

	intervalSeconds = Number(settings.tracking_interval) || DEFAULT_INTERVAL
	isNative = Capacitor.isNativePlatform()

	try {
		if (isNative) {
			await startNative()
		} else {
			startWeb()
		}
		startFlushTimer()
		trackingState.active = true
	} catch (err) {
		console.error("Failed to start location tracking:", err)
	}
}

/** Stop location tracking and flush any remaining pings. */
export async function stopTracking() {
	if (!trackingState.active) return
	trackingState.active = false

	if (isNative && nativeWatcherId) {
		try {
			await getBackgroundGeolocation().removeWatcher({ id: nativeWatcherId })
		} catch (err) {
			console.error("Failed to remove background watcher:", err)
		}
		nativeWatcherId = null
	}

	if (!isNative && webWatchId != null) {
		navigator.geolocation.clearWatch(webWatchId)
		webWatchId = null
	}

	stopFlushTimer()
	await flush()
}

export function isTracking() {
	return trackingState.active
}
