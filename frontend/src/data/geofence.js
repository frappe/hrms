import router from "@/router"
import { createResource } from "frappe-ui"

export const geofenceResource = createResource({
  url: "hrms.api.get_all_geofence",
  cache: "hrms:geofence",
  onError(error) {
    if (error && error.exc_type === "AuthenticationError") {
      router.push({ name: "Login" })
    }
  },
})