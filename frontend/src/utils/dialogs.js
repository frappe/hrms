export const showErrorAlert = async (message) => {
	const alert = await alertController.create({
		header: "Error",
		message,
		buttons: ["OK"],
	})

	await alert.present()
}

import { alertController } from "@ionic/vue"
