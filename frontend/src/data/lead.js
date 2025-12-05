import router from "@/router"
import { createResource } from "frappe-ui"

export const leadsResource = createResource({
  url: "hrms.api.get_all_leads",
  cache: "hrms:leads",
  onError(error) {
    if (error && error.exc_type === "AuthenticationError") {
      router.push({ name: "Login" })
    }
  },
})