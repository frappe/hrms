<script setup>
import { ref, onMounted } from "vue";
import { call, toast } from "frappe-ui";
const trips = ref([]);
const loading = ref(true);

const showModal = ref(false);

const selectedTrip = ref({});

const latitude = ref(null)
const longitude = ref(null)
const locationStatus = ref("")

async function loadTrips() {
    loading.value = true;

    try {
        // Get logged-in user
        const user = await call("frappe.auth.get_logged_user");

        // Find Driver linked to this user
        const drivers = await call("frappe.client.get_list", {
            doctype: "Driver",
            fields: ["name"],
            filters: {
                user: user,
            },
            limit_page_length: 1,
        });

        if (!drivers.length) {
            trips.value = [];
            return;
        }

        // Get Delivery Trips
        trips.value = await call("frappe.client.get_list", {
            doctype: "Delivery Trip",
            fields: [
                "name",
                "status",
                "vehicle",
                "driver_name",
                "departure_time",
                "lh_customer",
                "lh_source_city",
                "lh_destination_city",
                "lh_quantity",
                "lh_truck_type",
                "lh_source_map_url",
                "lh_destination_map_url",
            ],
            filters: {
                driver: drivers[0].name,
            },
            order_by: "creation desc",
        });
        console.log(trips.value)


    } catch (e) {
        console.error(e);
    } finally {
        loading.value = false;
    }
}

function getLocationFromMapUrl(url) {
  if (!url) return null

  const match = url.match(/q=([-0-9.]+),([-0-9.]+)/)

  if (!match) return null

  return {
    latitude: parseFloat(match[1]),
    longitude: parseFloat(match[2]),
  }
}

  function calculateDistance(lat1, lon1, lat2, lon2) {
    const toRadians = (degree) => degree * (Math.PI / 180)
    const R = 6371e3
  
    const φ1 = toRadians(lat1)
    const φ2 = toRadians(lat2)
    const Δφ = toRadians(lat2 - lat1)
    const Δλ = toRadians(lon2 - lon1)
  
    const a =
      Math.sin(Δφ / 2) * Math.sin(Δφ / 2) +
      Math.cos(φ1) * Math.cos(φ2) * Math.sin(Δλ / 2) * Math.sin(Δλ / 2)
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
  
    const distance = R * c
    return distance
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
async function validateLocation(mapUrl) {

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

        const destination = getLocationFromMapUrl(mapUrl)

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

        console.log("Distance", distance)

        const allowedDistance = 100

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

function openTrip(trip) {
    selectedTrip.value = trip;
    showModal.value = true;
}

async function startTrip() {
    console.log(selectedTrip.value)

    const canStart = await validateLocation(
        selectedTrip.value.lh_source_map_url
    )

    if (!canStart) return

    console.log("Start Trip")
}

async function endTrip() {
    const canEnd = await validateLocation(
        selectedTrip.value.lh_destination_map_url
    )

    if (!canEnd) return

    console.log("End Trip")
}


onMounted(loadTrips);
</script>

<template>
    <div class="p-4">
        <h2 class="text-xl font-bold mb-4">My Delivery Trips</h2>

        <div
            v-for="trip in trips"
            :key="trip.name"
            class="border rounded-lg p-4 mb-3 cursor-pointer"
            @click="openTrip(trip)"
        >
            <h3>{{ trip.name }}</h3>

            <p>{{ trip.lh_customer }}</p>

            <p>{{ trip.lh_source_city }} → {{ trip.lh_destination_city }}</p>

            <p>{{ trip.status }}</p>
        </div>

        <!-- Modal -->
        <div
            v-if="showModal"
            class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
        >
            <div class="bg-white rounded-xl w-80 p-5">

                <h2 class="text-lg font-bold mb-2">
                    {{ selectedTrip.name }}
                </h2>

                <p class="mb-5">
                    {{ selectedTrip.lh_customer }}
                </p>

                <button
                    class="w-full bg-green-600 text-white rounded-lg py-3 mb-3"
                    @click="startTrip(selectedTrip)"
                >
                    Start Trip
                </button>

                <button
                    class="w-full bg-red-600 text-white rounded-lg py-3 mb-3"
                    @click="endTrip(selectedTrip)"
                >
                    End Trip
                </button>

                <button
                    class="w-full border rounded-lg py-3"
                    @click="showModal = false"
                >
                    Cancel
                </button>

            </div>
        </div>

    </div>
</template>