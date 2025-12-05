import router from "@/router"
import { createResource } from "frappe-ui"

export const wfhResource = createResource({
  url: "hrms.api.get_all_wfh",
  cache: "hrms:wfh",
  onError(error) {
    if (error && error.exc_type === "AuthenticationError") {
      router.push({ name: "Login" })
    }
  },
})