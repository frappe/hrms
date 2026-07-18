import { ref } from "vue"
import { call, toast } from "frappe-ui"

// Reusable trip location/geofence check, extracted from the driver check-in logic.
export function useTripLocation() {
	const latitude = ref(null)
	const longitude = ref(null)
	const locationStatus = ref("")

	// Matches coordinates embedded directly in a URL, in any of the common
	// map link formats: ?q=lat,lng  ?ll=lat,lng  @lat,lng,zoom  ?mlat=..&mlon=..
	const COORD_PATTERNS = [
		/[?&]q=(-?\d+\.\d+),(-?\d+\.\d+)/,
		/[?&]ll=(-?\d+\.\d+),(-?\d+\.\d+)/,
		/@(-?\d+\.\d+),(-?\d+\.\d+)/,
		/[?&]mlat=(-?\d+\.\d+)[^&]*&mlon=(-?\d+\.\d+)/,
	]

	function getLocationFromMapUrl(url) {
		if (!url) return null

		for (const pattern of COORD_PATTERNS) {
			const match = url.match(pattern)
			if (match) {
				return {
					latitude: parseFloat(match[1]),
					longitude: parseFloat(match[2]),
				}
			}
		}

		return null
	}

	// Short links (maps.app.goo.gl, goo.gl, maps.google.com/...) don't carry
	// coordinates in the URL — they only resolve after Google's redirect,
	// which the browser can't read cross-origin. Ask the backend to expand
	// it instead. Requires a whitelisted method, e.g.:
	//
	//   @frappe.whitelist()
	//   def resolve_map_coordinates(url):
	//       import requests
	//       resp = requests.head(url, allow_redirects=True, timeout=5)
	//       match = re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", resp.url)
	//       if not match:
	//           return None
	//       return {"latitude": float(match.group(1)), "longitude": float(match.group(2))}
	//
	async function resolveShortMapUrl(url) {
		try {
			return await call("hrms.api.resolve_map_coordinates", { url })
		} catch {
			return null
		}
	}

	function calculateDistance(lat1, lon1, lat2, lon2) {
		const toRadians = (degree) => degree * (Math.PI / 180)
		const R = 6371e3

		const phi1 = toRadians(lat1)
		const phi2 = toRadians(lat2)
		const deltaPhi = toRadians(lat2 - lat1)
		const deltaLambda = toRadians(lon2 - lon1)

		const a =
			Math.sin(deltaPhi / 2) * Math.sin(deltaPhi / 2) +
			Math.cos(phi1) * Math.cos(phi2) * Math.sin(deltaLambda / 2) * Math.sin(deltaLambda / 2)
		const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))

		return R * c
	}

	function handleLocationSuccess(position) {
		latitude.value = position.coords.latitude
		longitude.value = position.coords.longitude
		locationStatus.value = "Location detected successfully."
	}

	function handleLocationError(error) {
		let message = "Unable to get your location."

		switch (error?.code) {
			case error.PERMISSION_DENIED:
				message = "Location permission denied. Please enable location access."
				break
			case error.POSITION_UNAVAILABLE:
				message = "Location information is unavailable."
				break
			case error.TIMEOUT:
				message = "Location request timed out."
				break
			default:
				message = "Unknown location error."
		}

		locationStatus.value = message

		toast({
			title: "Location Error",
			text: message,
			icon: "alert-circle",
			position: "bottom-center",
		})
	}

	function fetchLocation() {
		return new Promise((resolve, reject) => {
			if (!navigator.geolocation) {
				handleLocationError()
				reject()
				return
			}

			navigator.geolocation.getCurrentPosition(
				(position) => {
					handleLocationSuccess(position)
					resolve(position)
				},
				(error) => {
					handleLocationError(error)
					reject(error)
				},
				{
					enableHighAccuracy: true,
					timeout: 10000,
					maximumAge: 0,
				}
			)
		})
	}

	async function validateLocation(mapUrl, allowedDistance = 100) {
		if (!mapUrl) {
			toast({
				title: "Trip Location Missing",
				text: "This trip has no configured GPS location.",
				icon: "alert-circle",
				position: "bottom-center",
			})
			return false
		}

		try {
			await fetchLocation()

			let destination = getLocationFromMapUrl(mapUrl)

			if (!destination) {
				destination = await resolveShortMapUrl(mapUrl)
			}

			if (!destination) {
				toast({
					title: "Invalid Map URL",
					text: "Unable to read the trip coordinates.",
					icon: "alert-circle",
					position: "bottom-center",
				})
				return false
			}

			const distance = calculateDistance(
				latitude.value,
				longitude.value,
				destination.latitude,
				destination.longitude
			)

			if (distance > allowedDistance) {
				toast({
					title: "Wrong Location",
					text: `Move closer to the destination. You are ${Math.round(distance)} meters away.`,
					icon: "alert-circle",
					position: "bottom-center",
				})
				return false
			}

			toast({
				title: "Location Verified",
				text: "You are at the correct location.",
				position: "bottom-center",
			})
			return true
		} catch {
			return false
		}
	}

	return {
		latitude,
		longitude,
		locationStatus,
		fetchLocation,
		validateLocation,
	}
}