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
        <div class="h-120 w-full flex flex-col items-center justify-center gap-5 p-4 mb-5">
            <!-- Time and Date Display -->
            <div class="flex flex-col gap-1.5 mt-2 items-center justify-center">
                <div class="font-bold text-xl">
                    {{ dayjs(checkinTimestamp).format("hh:mm:ss a") }}
                </div>
                <div class="font-medium text-gray-500 text-sm">
                    {{ dayjs().format("D MMM, YYYY") }}
                </div>
            </div>

            <!-- Shift Location Dropdown or Message -->
            <div class="w-full" v-if="allowedLocations.length">
                <label for="custom_checkin_location" class="font-medium text-gray-700 text-sm">
                    {{ __("Select Shift Location") }}
                </label>
                <select
                    id="custom_checkin_location"
                    v-model="selectedLocation"
                    class="w-full mt-1 p-2 border rounded"
                    required
                >
                    <option value="" disabled>{{ __("Choose a location") }}</option>
                    <option
                        v-for="location in allowedLocations"
                        :key="location"
                        :value="location"
                    >
                        {{ location }}
                    </option>
                </select>
            </div>

            <!-- No Shift Location Fallback -->
            <div class="w-full text-center text-sm text-red-500 font-medium" v-else>
                {{ __("No shift locations assigned. Please contact HR.") }}
            </div>

            <!-- Shift Type Display (Read-Only) -->
            <div class="w-full" v-if="shiftType">
                <label for="shift_type" class="font-medium text-gray-700 text-sm">
                    {{ __("Shift Type") }}
                </label>
                <input
                    id="shift_type"
                    :value="shiftType"
                    class="w-full mt-1 p-2 border rounded bg-gray-100"
                    readonly
                />
            </div>

            <!-- Map View (Geolocation) -->
            <template v-if="settings.data?.allow_geolocation_tracking">
                <span v-if="locationStatus" class="font-medium text-gray-500 text-sm">
                    {{ locationStatus }}
                </span>

                <div class="rounded border-4 translate-z-0 block overflow-hidden w-full h-170">
                    <iframe
                        width="100%"
                        height="170"
                        frameborder="0"
                        scrolling="no"
                        marginheight="0"
                        marginwidth="0"
                        :src="`https://maps.google.com/maps?q=${latitude},${longitude}&hl=en&z=15&amp;output=embed`"
                    >
                    </iframe>
                </div>
            </template>

            <!-- Submit Button -->
            <Button
                variant="solid"
                class="w-full py-5 text-sm"
                :disabled="!selectedLocation || !allowedLocations.length"
                @click.once="submitLog(nextAction.action)"
            >
                {{ __("Confirm {0}", [nextAction.label]) }}
            </Button>
        </div>
    </ion-modal>
</template>

<script setup>
import { createResource, createListResource, toast, FeatherIcon } from "frappe-ui"
import { computed, inject, ref, onMounted, onBeforeUnmount, watch } from "vue"
import { IonModal, modalController } from "@ionic/vue"
import { formatTimestamp } from "@/utils/formatters"

const DOCTYPE = "Employee Checkin"

const socket = inject("$socket")
const employee = inject("$employee")
const dayjs = inject("$dayjs")
const __ = inject("$translate")
const checkinTimestamp = ref(null)
const latitude = ref(0)
const longitude = ref(0)
const locationStatus = ref("")
const selectedLocation = ref("")
const allowedLocations = ref([])
const shiftType = ref("")

const settings = createResource({
    url: "hrms.api.get_hr_settings",
    auto: true,
})

const checkins = createListResource({
    doctype: DOCTYPE,
    fields: ["name", "employee", "employee_name", "log_type", "time", "device_id", "custom_checkin_location"],
    filters: {
        employee: employee.data.name,
    },
    orderBy: "time desc",
})

const allowedLocationsResource = createResource({
    url: "frappe.client.get",
    params: {
        doctype: "Employee",
        name: employee.data.name,
        fields: ["custom_allowed_shift_locations"],
    },
    onSuccess(data) {
        console.log("Fetching allowed shift locations for employee:", employee.data.name);
        console.log("Allowed shift locations data:", data);
        allowedLocations.value = (data.custom_allowed_shift_locations || []).map(row => row.shift_location).filter(Boolean)
        console.log("Processed allowedLocations:", allowedLocations.value);
        if (allowedLocations.value.length > 0 && !selectedLocation.value) {
            selectedLocation.value = allowedLocations.value[0]
            console.log("Set default selectedLocation:", selectedLocation.value);
        }
        if (selectedLocation.value && !allowedLocations.value.includes(selectedLocation.value)) {
            selectedLocation.value = allowedLocations.value[0] || ""
            console.log("Reset selectedLocation to:", selectedLocation.value);
        }
    },
    onError(error) {
        console.error("Error fetching allowed shift locations:", error);
        toast({
            title: __("Error"),
            text: __("Failed to fetch allowed shift locations"),
            icon: "alert-circle",
            position: "bottom-center",
            iconClasses: "text-red-500",
        })
    },
})

const shiftTypeResource = createResource({
    url: "frappe.client.get_list",
    params: {
        doctype: "Shift Assignment",
        filters: {
            employee: () => {
                console.log("Employee name for Shift Assignment query:", employee.data.name);
                return employee.data.name;
            },
            start_date: () => {
                const startDate = dayjs().format("YYYY-MM-DD");
                console.log("Start date filter:", startDate);
                return ["<=", startDate];
            },
            end_date: () => {
                const endDate = dayjs().format("YYYY-MM-DD");
                console.log("End date filter:", endDate);
                return [">=", endDate];
            },
            shift_location: () => {
                console.log("Shift location filter:", selectedLocation.value);
                return selectedLocation.value;
            },
            docstatus: 1,
        },
        fields: ["shift_type", "name", "start_date", "end_date", "shift_location"],
        limit: 1,
    },
    onSuccess(data) {
        console.log("Fetching Shift Type for employee:", employee.data.name);
        console.log("Shift Assignment full data:", data);

        const matchedAssignment = data.find(
            assignment => assignment.shift_location === selectedLocation.value
        );

        if (matchedAssignment) {
            shiftType.value = matchedAssignment.shift_type;
            console.log("Matched shift type:", shiftType.value);
        } else {
            shiftType.value = "Day"; // fallback
            console.warn("No matching shift assignment found for location:", selectedLocation.value);
        }
    },
    onError(error) {
        console.error("Error fetching Shift Type:", error);
        shiftType.value = "Day"; // Default to "Day" on error
        console.log("Set default shiftType on error:", shiftType.value);
        toast({
            title: __("Error"),
            text: __("Failed to fetch Shift Type, using default 'Day'"),
            icon: "alert-circle",
            position: "bottom-center",
            iconClasses: "text-red-500",
        })
    },
})

watch(selectedLocation, (newLocation) => {
    console.log("Selected location changed:", newLocation);
    if (newLocation) {
        shiftTypeResource.fetch();
        console.log("Refetched Shift Type for location:", newLocation);
    }
})

onMounted(() => {
    console.log("Component mounted, employee:", employee.data);
    console.log("Fetching resources...");
    allowedLocationsResource.fetch()
    shiftTypeResource.fetch()
    socket.emit("doctype_subscribe", DOCTYPE)
    socket.on("list_update", (data) => {
        if (data.doctype == DOCTYPE) {
            checkins.reload()
        }
    })
})

onBeforeUnmount(() => {
    socket.emit("doctype_unsubscribe", DOCTYPE)
    socket.off("list_update")
})

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
    console.log("Geolocation success:", locationStatus.value);
}

function handleLocationError(error) {
    locationStatus.value = "Unable to retrieve your location"
    if (error) locationStatus.value += `: ERROR(${error.code}): ${error.message}`
    console.error("Geolocation error:", locationStatus.value);
}

const fetchLocation = () => {
    if (!navigator.geolocation) {
        locationStatus.value = __("Geolocation is not supported by your current browser")
        console.error("Geolocation not supported");
    } else {
        locationStatus.value = __("Locating...")
        navigator.geolocation.getCurrentPosition(handleLocationSuccess, handleLocationError)
    }
}

const handleEmployeeCheckin = () => {
    checkinTimestamp.value = dayjs().format("YYYY-MM-DD HH:mm:ss")
    console.log("Opening check-in modal, timestamp:", checkinTimestamp.value);
    if (settings.data?.allow_geolocation_tracking) {
        fetchLocation()
    }
    shiftTypeResource.fetch()
    console.log("Refetched Shift Type on modal open");
}

const submitLog = (logType) => {
    const actionLabel = logType === "IN" ? __("Check-in") : __("Check-out")
    const payload = {
        employee: employee.data.name,
        log_type: logType,
        time: checkinTimestamp.value,
        latitude: latitude.value,
        longitude: longitude.value,
        custom_checkin_location: selectedLocation.value,
        shift: shiftType.value,
    }
    console.log("Submitting check-in with payload:", payload);

    checkins.insert.submit(
        payload,
        {
            onSuccess() {
                console.log("Check-in submitted successfully");
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
                console.error("Check-in submission error:", error);
                toast({
                    title: __("Error"),
                    text: `${actionLabel} failed! ${error.messages?.[0] || ""}`,
                    icon: "alert-circle",
                    position: "bottom-center",
                    iconClasses: "text-red-500",
                })
            },
        }
    )
}
</script>
