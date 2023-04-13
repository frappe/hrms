import { createApp } from "vue"
import App from "./App.vue"
import router from "./router"

import { Button, setConfig, frappeRequest, resourcesPlugin } from "frappe-ui"

import { IonicVue } from "@ionic/vue"

/* Core CSS required for Ionic components to work properly */
import "@ionic/vue/css/core.css"

/* Theme variables */
import "./theme/variables.css"

import "./main.css"

const app = createApp(App)
	.use(IonicVue)
	.use(router)

setConfig("resourceFetcher", frappeRequest)

app.use(resourcesPlugin)

app.component("Button", Button)

router.isReady().then(() => {
	app.mount("#app");
})
