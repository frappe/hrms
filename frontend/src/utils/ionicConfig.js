import { isPlatform } from "@ionic/vue"
import { createAnimation, iosTransitionAnimation } from "@ionic/core"
/**
 * on iOS, the back swipe gesture triggers the animation twice:
 * the safari's default back swipe animation & ionic's animation
 * The config here takes care of the same
 */

export const animationBuilder = (baseEl, opts) => {
	if (opts.direction === "back") {
		/**
		 * Even after disabling swipeBackEnabled, when the swipe is completed & we're back on the first screen
		 * the "pop" animation is triggered, resulting in a double animation
		 * HACK: return empty animation for back swipe in ios
		 **/
		return createAnimation()
	}

	return iosTransitionAnimation(baseEl, opts)
}

const getIonicConfig = () => {
	const config = { mode: "ios" }

	if (isPlatform("iphone")) {
		// disable ionic's swipe back gesture on ios
		config.swipeBackEnabled = false
		config.navAnimation = animationBuilder
	}

	return config
}

export default getIonicConfig
