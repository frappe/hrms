import router from "@/router"
import { createResource } from "frappe-ui"

export const locationResource = createResource({
  url: "hrms.api.get_all_location",
  cache: "hrms:location",
  onError(error) {
    if (error && error.exc_type === "AuthenticationError") {
      router.push({ name: "Login" })
    }
  },
})