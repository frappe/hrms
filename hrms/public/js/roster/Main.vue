<script setup>
import { ref, onMounted, computed } from "vue";
import ProvisionalPlan from "./components/ProvisionalPlan.vue";
import EmployeesFilter from "./components/EmployeesFilter.vue";
import EmployeesPool from "./components/EmployeesPool.vue";
import RosterWeekly from "./components/RosterWeekly.vue";
import MonthlyProvisional from "./components/MonthlyProvisional.vue";
import moment from "moment";
import { inject } from "vue";

const R = "R"; //rest day
const D = "D"; //jour
const N = "N"; //nuit

const shift = ref([]);
const title = ref(null);
const startDate = ref(new Date());

const frm = inject("frm");

const onProvionalPlanChange = (value) => {
  startDate.value = new Date(value.start_date);
  title.value = value.title;
};

const employeesFilter = ref({
  company: undefined,
  department: undefined,
  designation: undefined,
});
const onEmployeeFilterChange = (value) => {
  employeesFilter.value = value;
};

const employees = ref([]);

const validateMonthlyView = computed(() => {
  if (shift.value.length === employees.value.length && shift.value.length > 0) {
    for (const emp of employees.value) {
      if (!emp || emp.length === 0) {
        return false;
      }
    }
    return true;
  }
  return false;
});
const startOfMonth = computed(() => {
  return new Date(startDate.value.getFullYear(), startDate.value.getMonth(), 1);
});
const validateShift = computed(() => {
  const fshifts = shift.value.flat(1);
  return fshifts.filter((s) => s === D || s === N).length > 0;
});
const canSave = computed(() => {
  return (
    validateMonthlyView.value &&
    !!title.value &&
    title.value.length > 0 &&
    employees.value.length === shift.value.length &&
    validateShift.value
  );
});

const onSaveAction = async () => {
  frm.set_value("title", title.value);
  frm.set_value("start_date", moment(startDate.value).format("YYYY-MM-DD"));
  frm.set_value("shifts", JSON.stringify(shift.value));
  frm.set_value("employees", employees.value);
  frm.set_value("department", employeesFilter.value.department);
  frm.set_value("shift_department", shiftDeparment.value);
  frm.set_value("month", moment(startOfMonth.value).format("MMM"));
  frm.set_value("year", moment(startOfMonth.value).format("YYYY"));
  frm.save();
  frm.call("sync").then(() => {
    frm.reload_doc();
  });
};

const shiftDeparment = ref();
const onShiftDeparmentChange = (value) => {
  shiftDeparment.value = value;
};
</script>
<template>
  <div>
    <div class="form-page">
      <div class="d-flex flex-row justify-content-end align-items-center w-100">
        <div class="pr-4">{{ moment(startOfMonth).format("MMM YYYY") }}</div>
        <button
          class="btn btn-primary"
          :disabled="!canSave"
          @click="onSaveAction"
        >
          Save Provisional Plan
        </button>
      </div>
      <ProvisionalPlan
        @change="onProvionalPlanChange"
        :startDate="startDate"
        :title="title"
      />
      <EmployeesFilter @change="onEmployeeFilterChange" />
      <EmployeesPool :filter="employeesFilter" v-model:selected="employees" />
      <RosterWeekly
        v-model:shift="shift"
        :start-date="startDate"
        v-model:employees="employees"
        @depchange="onShiftDeparmentChange"
      />
      <MonthlyProvisional
        v-if="validateMonthlyView"
        :shifts="shift"
        :shiftDeparment="shiftDeparment"
        :employees="employees"
        :startDate="startDate"
      />
      <div style="height: 100px"></div>
    </div>
  </div>
</template>
