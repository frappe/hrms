import { createApp } from "vue";
import App from "./App.vue";

class Roster {
  constructor({ frm, wrapper }) {
    this.frm = frm;
    this.$wrapper = $(wrapper);
    this.init();
  }

  init() {
    this.setup_app();
  }

  setup_app() {
    if (this.$wrapper.get(0).__vue__app !== undefined) {
      console.log("Vue app already mounted");
    } else {
      // create a vue instance

      let app = createApp(App);
      app.provide("frm", this.frm);
      // mount the app
      this.$roster = app.mount(this.$wrapper.get(0));
      this.app = app;
    }
  }
}

frappe.provide("frappe.ui");
frappe.ui.Roster = Roster;
export default Roster;
