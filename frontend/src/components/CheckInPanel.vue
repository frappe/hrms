<template>
	<div class="flex flex-col bg-white rounded w-full py-6 px-4 border-none">
		<h2 class="text-lg font-bold text-gray-900">
			{{ __("Hey, {0} 👋", [employee?.data?.first_name]) }}
		</h2>

		<template v-if="settings.data?.allow_employee_checkin_from_mobile_app">
			<div class="font-medium text-sm text-gray-500 mt-1.5" v-if="lastLog">
				<span>{{ __("Last {0} was at {1}", [__(lastLogType), formatTimestamp(lastLog.time)]) }}</span>
				<span class="whitespace-pre"> &middot; </span>
				<router-link :to="{ name: 'EmployeeCheckinListView' }" v-slot="{ navigate }">
					<span @click="navigate" class="underline">View List</span>
				</router-link>
			</div>
			<Button
				class="mt-4 mb-1 drop-shadow-sm py-5 text-base"
				id="open-checkin-modal"
				@click="handleEmployeeCheckin"
			>
				<template #prefix>
					<FeatherIcon
						:name="nextAction.action === 'IN' ? 'arrow-right-circle' : 'arrow-left-circle'"
						class="w-4"
					/>
				</template>
				{{ nextAction.label }}
			</Button>
		</template>

		<div v-else class="font-medium text-sm text-gray-500 mt-1.5">
			{{ dayjs().format("ddd, D MMMM, YYYY") }}
		</div>
	</div>

	<ion-modal
		v-if="settings.data?.allow_employee_checkin_from_mobile_app"
		ref="modal"
		trigger="open-checkin-modal"
		:initial-breakpoint="1"
		:breakpoints="[0, 1]"
	>
		<div class="w-full flex flex-col gap-4 p-4 pb-8">

			<!-- Time & Date -->
			<div class="flex flex-col gap-1 items-center justify-center mt-2">
				<div class="font-bold text-2xl">
					{{ dayjs(checkinTimestamp).format("hh:mm:ss a") }}
				</div>
				<div class="font-medium text-gray-500 text-sm">
					{{ dayjs().format("dddd, D MMMM YYYY") }}
				</div>
			</div>

			<!-- Geolocation -->
			<template v-if="settings.data?.allow_geolocation_tracking">
				<span v-if="locationStatus" class="font-medium text-gray-500 text-xs text-center">
					{{ locationStatus }}
				</span>
				<div class="rounded-xl overflow-hidden w-full" style="height: 140px;">
					<iframe
						width="100%"
						height="140"
						frameborder="0"
						scrolling="no"
						style="border: 0; border-radius: 12px;"
						:src="`https://maps.google.com/maps?q=${latitude},${longitude}&hl=en&z=15&amp;output=embed`"
					/>
				</div>
			</template>

			<!-- Camera Section -->
			<div class="w-full flex flex-col gap-3">

				<!-- Camera label -->
				<div class="flex items-center gap-2">
					<span class="text-sm font-semibold text-gray-700">📷 Check-in Photo</span>
					<span v-if="photoData" class="text-xs text-green-600 font-medium">✓ Captured</span>
				</div>

				<!-- Live camera preview -->
				<div
					v-if="cameraActive"
					class="w-full rounded-2xl overflow-hidden bg-black relative"
					style="aspect-ratio: 4/3;"
				>
					<video
						ref="videoRef"
						autoplay
						playsinline
						muted
						class="w-full h-full object-cover"
					></video>
					<!-- Capture button overlay -->
					<div class="absolute bottom-3 left-0 right-0 flex justify-center">
						<button
							@click="capturePhoto"
							class="w-14 h-14 rounded-full bg-white border-4 border-gray-300 shadow-lg flex items-center justify-center"
							style="box-shadow: 0 0 0 3px rgba(255,255,255,0.5);"
						>
							<div class="w-10 h-10 rounded-full bg-white border-2 border-gray-400"></div>
						</button>
					</div>
				</div>

				<!-- Photo preview after capture -->
				<div
					v-if="photoData && !cameraActive"
					class="w-full rounded-2xl overflow-hidden relative"
					style="aspect-ratio: 4/3;"
				>
					<img
						:src="photoData"
						class="w-full h-full object-cover"
					/>
					<!-- Retake overlay button -->
					<button
						@click="retakePhoto"
						class="absolute top-2 right-2 bg-black bg-opacity-50 text-white text-xs px-3 py-1.5 rounded-full font-medium"
					>
						🔄 Retake
					</button>
				</div>

				<!-- Placeholder when no camera active and no photo -->
				<div
					v-if="!cameraActive && !photoData"
					class="w-full rounded-2xl bg-gray-100 flex flex-col items-center justify-center gap-2 cursor-pointer"
					style="aspect-ratio: 4/3;"
					@click="startCamera"
				>
					<span class="text-4xl">📷</span>
					<span class="text-sm text-gray-500 font-medium">Tap to open camera</span>
				</div>

				<!-- Error message -->
				<div v-if="cameraError" class="bg-red-50 border border-red-200 rounded-xl px-3 py-2">
					<p class="text-red-600 text-sm text-center">{{ cameraError }}</p>
				</div>

			</div>

			<!-- Confirm Button -->
			<Button
				:loading="checkins.insert.loading"
				variant="solid"
				class="w-full py-5 text-base font-semibold mt-2"
				@click="submitLog(nextAction.action)"
			>
				{{ __("Confirm {0}", [nextAction.label]) }}
			</Button>

		</div>
	</ion-modal>
</template>

<script setup>
import { createListResource, toast, FeatherIcon } from "frappe-ui"
import { computed, inject, ref, onMounted, onBeforeUnmount, nextTick } from "vue"
import { IonModal, modalController } from "@ionic/vue"

import { formatTimestamp } from "@/utils/formatters"
import { settings } from "@/data/settings"

const DOCTYPE = "Employee Checkin"

const socket = inject("$socket")
const employee = inject("$employee")
const dayjs = inject("$dayjs")
const __ = inject("$translate")

const checkinTimestamp = ref(null)
const latitude = ref(0)
const longitude = ref(0)
const locationStatus = ref("")

// Camera state
const videoRef = ref(null)
const cameraActive = ref(false)
const photoData = ref(null)
const cameraError = ref("")
let stream = null

const checkins = createListResource({
	doctype: DOCTYPE,
	fields: ["name", "employee", "employee_name", "log_type", "time", "device_id"],
	filters: { employee: employee.data.name },
	orderBy: "time desc",
})
checkins.reload()

const lastLog = computed(() => {
	if (checkins.list.loading || !checkins.data) return {}
	return checkins.data[0]
})

const lastLogType = computed(() => {
	return lastLog?.value?.log_type === "IN" ? "check-in" : "check-out"
})

const nextAction = computed(() => {
	return lastLog?.value?.log_type === "IN"
		? { action: "OUT", label: __("Check Out") }
		: { action: "IN", label: __("Check In") }
})

function handleLocationSuccess(position) {
	latitude.value = position.coords.latitude
	longitude.value = position.coords.longitude
	locationStatus.value = [
		__("Latitude: {0}°", [Number(latitude.value).toFixed(5)]),
		__("Longitude: {0}°", [Number(longitude.value).toFixed(5)]),
	].join(", ")
}

function handleLocationError(error) {
	locationStatus.value = "Unable to retrieve your location"
	if (error) locationStatus.value += `: ERROR(${error.code}): ${error.message}`
}

const fetchLocation = () => {
	if (!navigator.geolocation) {
		locationStatus.value = __("Geolocation is not supported by your current browser")
	} else {
		locationStatus.value = __("Locating...")
		navigator.geolocation.getCurrentPosition(handleLocationSuccess, handleLocationError)
	}
}

const handleEmployeeCheckin = () => {
	checkinTimestamp.value = dayjs().format("YYYY-MM-DD HH:mm:ss")
	photoData.value = null
	cameraActive.value = false
	cameraError.value = ""
	if (settings.data?.allow_geolocation_tracking) {
		fetchLocation()
	}
}

const startCamera = async () => {
	cameraError.value = ""
	try {
		stream = await navigator.mediaDevices.getUserMedia({
			video: { facingMode: "user", width: { ideal: 1280 }, height: { ideal: 960 } },
			audio: false,
		})
		cameraActive.value = true
		await nextTick()
		if (videoRef.value) {
			videoRef.value.srcObject = stream
		}
	} catch (err) {
		if (err.name === "NotAllowedError") {
			cameraError.value = __("Camera permission denied. Please allow camera access and try again.")
		} else if (err.name === "NotFoundError") {
			cameraError.value = __("No camera found on this device.")
		} else {
			cameraError.value = __("Could not access camera: ") + err.message
		}
	}
}

const capturePhoto = () => {
	if (!videoRef.value) return
	const canvas = document.createElement("canvas")
	canvas.width = videoRef.value.videoWidth
	canvas.height = videoRef.value.videoHeight
	canvas.getContext("2d").drawImage(videoRef.value, 0, 0)

	// Compress if > 1MB
	let quality = 0.85
	let dataUrl = canvas.toDataURL("image/jpeg", quality)
	while (dataUrl.length > 1_000_000 && quality > 0.2) {
		quality -= 0.1
		dataUrl = canvas.toDataURL("image/jpeg", quality)
	}

	photoData.value = dataUrl
	stopCamera()
}

const retakePhoto = () => {
	photoData.value = null
	startCamera()
}

const stopCamera = () => {
	if (stream) {
		stream.getTracks().forEach(track => track.stop())
		stream = null
	}
	cameraActive.value = false
}

const submitLog = (logType) => {
	const actionLabel = logType === "IN" ? __("Check-in") : __("Check-out")

	checkins.insert.submit(
		{
			employee: employee.data.name,
			log_type: logType,
			time: checkinTimestamp.value,
			latitude: latitude.value,
			longitude: longitude.value,
			custom_check_in_photo: photoData.value || "",
		},
		{
			onSuccess() {
				stopCamera()
				photoData.value = null
				modalController.dismiss()
				toast({
					title: __("Success"),
					text: __("{0} successful!", [actionLabel]),
					icon: "check-circle",
					position: "bottom-center",
					iconClasses: "text-green-500",
				})
			},
			onError(error) {
				let messages = error.messages || []
				for (const message of messages) {
					toast({
						title: __("Error"),
						text: message || __("{0} failed!", [actionLabel]),
						icon: "alert-circle",
						position: "bottom-center",
						iconClasses: "text-red-500",
					})
				}
			},
		}
	)
}

onMounted(() => {
	socket.emit("doctype_subscribe", DOCTYPE)
	socket.on("list_update", (data) => {
		if (data.doctype == DOCTYPE) {
			checkins.reload()
		}
	})
})

onBeforeUnmount(() => {
	stopCamera()
	socket.emit("doctype_unsubscribe", DOCTYPE)
	socket.off("list_update")
})
</script>