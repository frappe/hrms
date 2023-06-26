# Frappe UI Starter

This template should help get you started developing custom frontend for Frappe
apps with Vue 3 and the Frappe UI package.

This boilerplate sets up Vue 3, Vue Router, TailwindCSS, and Frappe UI out of
the box.

## Usage

This template is meant to be cloned inside an existing Frappe App. Assuming your
apps name is `todo`. Clone this template in the root folder of your app using `degit`.

```
cd apps/todo
npx degit netchampfaris/frappe-ui-starter frontend
cd frontend
yarn
yarn dev
```

In a development environment, you need to put the below key-value pair in your `site_config.json` file:

```
"ignore_csrf": 1
```

This will prevent `CSRFToken` errors while using the vite dev server. In production environment, the `csrf_token` is attached to the `window` object in `index.html` for you.

The Vite dev server will start on the port `8080`. This can be changed from `vite.config.js`.
The development server is configured to proxy your frappe app (usually running on port `8000`). If you have a site named `todo.test`, open `http://todo.test:8080` in your browser. If you see a button named "Click to send 'ping' request", congratulations!

If you notice the browser URL is `/frontend`, this is the base URL where your frontend app will run in production.
To change this, open `src/router.js` and change the base URL passed to `createWebHistory`.

## Resources

- [Vue 3](https://v3.vuejs.org/guide/introduction.html)
- [Vue Router](https://next.router.vuejs.org/guide/)
- [Frappe UI](https://github.com/frappe/frappe-ui)
- [TailwindCSS](https://tailwindcss.com/docs/utility-first)
- [Vite](https://vitejs.dev/guide/)
