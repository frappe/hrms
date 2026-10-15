import { __ } from "@/plugins/translationsPlugin"
export const showErrorAlert = async (message) => {
	const alert = await alertController.create({
		header: __("Error"),
		message,
		buttons: ["OK"],
	})

	await alert.present()
}

import { alertController } from "@ionic/vue"
