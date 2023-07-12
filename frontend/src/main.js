import { createApp } from "vue"
import App from "./App.vue"
import router from "./router"
import socket from "./socket"

import {
	Button,
	Input,
	setConfig,
	frappeRequest,
	resourcesPlugin,
} from "frappe-ui"

import { IonicVue } from "@ionic/vue"

import { session } from "./data/session"
import { userResource } from "./data/user"
import { employeeResource } from "./data/employee"
import dayjs from "@/utils/dayjs"

/* Core CSS required for Ionic components to work properly */
import "@ionic/vue/css/core.css"

/* Theme variables */
import "./theme/variables.css"

import "./main.css"

const app = createApp(App)

setConfig("resourceFetcher", frappeRequest)
app.use(resourcesPlugin)

app.component("Button", Button)
app.component("Input", Input)

app.use(router)
app.use(IonicVue)

app.provide("$session", session)
app.provide("$user", userResource)
app.provide("$employee", employeeResource)
app.provide("$socket", socket)
app.provide("$dayjs", dayjs)

router.isReady().then(() => {
	app.mount("#app")
})
