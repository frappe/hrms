import {initializeApp} from "https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js";
import {getMessaging, onBackgroundMessage} from "https://www.gstatic.com/firebasejs/10.7.1/firebase-messaging-sw.js";

const jsonConfig = new URL(location).searchParams.get('config');
const firebaseApp = initializeApp(JSON.parse(jsonConfig));
const messaging = getMessaging(firebaseApp);
function isChrome() {
	return navigator.userAgent.toLowerCase().includes("chrome")
}
onBackgroundMessage(messaging, (payload) => {
	const notificationTitle = payload.data.title;
	let notificationOptions = {
		body: payload.data.body || ''
	};
	if (isChrome()) {
		notificationOptions['data'] = {
			url: payload.data.click_action
		}
	} else {
		if(payload.data.click_action){
			notificationOptions['actions'] = [{
				action: payload.data.click_action,
				title: 'View details'
			}]
		}
	}
	self.registration.showNotification(notificationTitle, notificationOptions);
});


if(isChrome()) {
	self.addEventListener('notificationclick', (event) => {
		event.stopImmediatePropagation();
		event.notification.close();
		if (event.notification.data && event.notification.data.url) {
			clients.openWindow(event.notification.data.url)
		}
	})
}