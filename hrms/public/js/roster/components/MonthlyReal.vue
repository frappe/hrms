<script setup lang="ts">
import { ref, computed, defineProps, onMounted } from "vue";
import moment from "moment";
import { inject } from "vue";
const frm = inject("frm");
const props = defineProps([
  "shifts",
  "employees",
  "startDate",
  "reals",
  "department",
  "showProvisionalShifts",
]);
const startDateIndex = computed(() => {
  const d = new Date(
    props.startDate.setDate(
      props.startDate.getDate() - props.startDate.getDay()
    )
  );
  return new Date(d.setDate(d.getDate() + 1)).getDate();
});
const startOfMonth = computed(() => {
  return new Date(props.startDate.getFullYear(), props.startDate.getMonth(), 1);
});
const numberOfDaysInMonth = computed(() => {
  return new Date(
    props.startDate.getFullYear(),
    props.startDate.getMonth() + 1,
    0
  ).getDate();
});

const numberOfEmployees = computed(() => {
  return props.shifts.length;
});

const uShifts = computed(() => {
  return props.shifts.flat(1);
});

const getShift = (i, ei) => {
  const value = (i - (startDateIndex.value - ei * 7)) % uShifts.value.length;
  if (value >= 0) {
    return uShifts.value[value];
  } else {
    return uShifts.value[uShifts.value.length + value];
  }
};
const update = ref(0);
const computedShifts = computed(() => {
  update.value;
  return Array(numberOfEmployees.value)
    .fill(0)
    .map((_, i) => {
      return JSON.parse(frm.doc.employees[i].shift);

      return Array(numberOfDaysInMonth.value)
        .fill(0)
        .map((_, j) => {
          return getShift(j + 1, i);
        });
    });
});

const computedReals = computed(() => {
  return Array(numberOfEmployees.value)
    .fill(0)
    .map((_, i) => {
      return Array(numberOfDaysInMonth.value)
        .fill(0)
        .map((_, j) => {
          if (props.reals[i] && props.reals[i][j].length > 0) {
            const r = props.reals[i][j]
              .map((r) => {
                return r.type;
              })
              .join(" + ");

            if (r.includes("L")) {
              return "L";
            } else {
              return r;
            }
          }
          return undefined;
        });
    });
});

const hoursWorked = (arr) => {
  let result = 0;
  for (let a of arr) {
    if (shiftsMap.value && shiftsMap.value[a]) {
      result += shiftsMap.value[a].effective_hours;
    }
  }
  return result;
};

const computedMonthlyHours = computed(() => {
  return computedShifts.value.map((shift) => {
    return hoursWorked(shift);
  });
});

const computedRealMonthlyHours = computed(() => {
  return props.reals.map((real) => {
    return real
      .map((r) => {
        return r
          .map((s) => {
            if (shiftsMap.value && shiftsMap.value[s.type]) {
              return shiftsMap.value[s.type].effective_hours;
            } else {
              return 0;
            }
          })
          .reduce((a, b) => a + b, 0);
      })
      .reduce((a, b) => a + b, 0);
  });
});

const activeWorking = (index, shift) => {
  const res = {};
  let total = 0;
  for (const element of shift) {
    const s = element;
    if (s[index - 1] !== "R") {
      total += 1;
      if (res[s[index - 1]]) {
        res[s[index - 1]] += 1;
      } else {
        res[s[index - 1]] = 1;
      }
    }
  }
  res.t = total;
  return Object.entries(res)
    .map(([key, value]) => `${key.toUpperCase()}: ${value}`)
    .join("\n");
};

const activeRealWorking = (index, shift) => {
  let d = 0;
  let n = 0;
  for (const element of shift) {
    const s = element[index - 1];
    for (const shift of s) {
      switch (shift.type) {
        case "D":
          d++;
          break;
        case "N":
          n++;
          break;
        case "L":
          if (shift.shift_type === "D") {
            d--;
          } else if (shift.shift_type === "N") {
            n--;
          }
          break;
        default:
          break;
      }
    }
  }
  return `${d}D ${n}N T:${d + n}`;
};

onMounted(() => {
  fetchShifts();
});
const depShifts = ref([]);
const shiftsMap = ref({});
const fetchShifts = () => {
  depShifts.value = [];
  //fetch shifts
  frappe.db
    .get_list("Shift Type", {
      filters: { department: frm.doc.shift_department },
      fields: ["*"],
      limit: 0,
    })
    .then((res) => {
      depShifts.value = res;
      shiftsMap.value = res.reduce((acc, shift) => {
        acc[shift.shift_suffix] = shift;
        return acc;
      }, {});
    });
};

const validate = (event) => {
  let valids = [];
  if (depShifts.value) valids = depShifts.value.map((s) => s.shift_suffix);
  valids.push("R");

  valids = [...valids, ...valids.map((v) => v.toLowerCase())];
  if (valids.indexOf(event.key) === -1) {
    event.preventDefault();
  } else {
    event.target.innerText = "";
  }
};

const input = (event, row, col) => {
  event.target.innerText = event.target.innerText.toUpperCase();
  console.log(row, col);
  // frm.doc.employees[row].shift[col] = event.target.innerText;
  // frm.doc.save();
  const shifts = JSON.parse(frm.doc.employees[row].shift);
  shifts[col] = event.target.innerText;
  const c = [...shifts];
  console.log(frm.doc.employees[row].name);
  console.log(c);
  frappe.model.set_value(
    "Provisional Plan Employee",
    frm.doc.employees[row].name,
    "shift",
    JSON.stringify(c)
  );
  // computedShifts.value[row][col] = event.target.innerText;
  frm.doc.employees[row].shift = JSON.stringify(c);
  update.value++;
  // frappe.db.commit();

  // const c = [...props.shift];
  // c[row][col] = event.target.innerText;
  // emits("update:shift", c);
};
</script>
<template>
  <div class="shifts mb-4">
    <h3>Shift Suffix</h3>
    <div v-for="shift in depShifts" class="shift flex">
      <div class="font-bold pl-2">{{ shift.shift_suffix }}</div>
      <div class="px-2">{{ shift.start_time }} - {{ shift.end_time }}</div>
    </div>
  </div>
  <h2 class="mx-auto text-center py-4">
    {{ moment(startOfMonth).format("MMM YYYY") }}
  </h2>
  <div class="w-100 table-responsive">
    <table class="table table-borderless table-sticky w-auto">
      <thead>
        <tr class="border">
          <th scope="col" class="text-nowrap">Employee Name</th>
          <th scope="col" class="text-nowrap">Hrs</th>
          <th
            v-for="i in numberOfDaysInMonth"
            scope="col"
            class="text-center text-sm"
            :class="{
              'bg-danger text-white': startDateIndex === i,
            }"
          >
            {{ i }}
          </th>
        </tr>
        <tr class="border">
          <th scope="col" class="text-nowrap">Day</th>
          <th scope="col" class="text-nowrap"></th>
          <th
            v-for="i in numberOfDaysInMonth"
            scope="col"
            class="text-center"
            :class="{
              'bg-danger text-white': startDateIndex === i,
            }"
          >
            {{
              moment(startOfMonth)
                .add(i - 1, "d")
                .format("ddd")
            }}
          </th>
        </tr>
      </thead>
      <tbody>
        <template v-for="(e, ei) in numberOfEmployees">
          <tr class="border-top">
            <th scope="row" class="text-nowrap border-left">
              {{ props.employees[ei].employee_name }}
            </th>
            <td scope="row" class="text-center">
              {{ computedMonthlyHours[ei] }}
            </td>
            <td
              v-for="i in numberOfDaysInMonth"
              class="text-center"
              :class="{
                'bg-red-100': computedShifts[ei][i - 1] === 'R',
                'bg-green-100': computedShifts[ei][i - 1] === 'D',
                'bg-green-300': computedShifts[ei][i - 1] === 'N',
              }"
              contenteditable="true"
              @keypress="validate"
              @paste.prevent=""
              @input="(event) => input(event, ei, i - 1)"
            >
              {{ computedShifts[ei][i - 1] }}
            </td>
          </tr>
          <tr v-if="!props.showProvisionalShifts">
            <td class="text-nowrap border-left">
              {{ props.employees[ei].name }}
            </td>
            <td
              class="text-center"
              :class="{
                'bg-danger text-white':
                  computedMonthlyHours[ei] > computedRealMonthlyHours[ei],
                'bg-success text-white':
                  computedMonthlyHours[ei] < computedRealMonthlyHours[ei],
              }"
            >
              {{ computedRealMonthlyHours[ei] }}
            </td>
            <td
              v-for="i in numberOfDaysInMonth"
              class="text-center"
              :class="{
                'bg-danger text-white': computedReals[ei][i - 1] === 'L',
                'bg-success text-white':
                  computedReals[ei][i - 1] &&
                  computedReals[ei][i - 1].includes('+'),
                // 'bg-green-100': computedReals[ei][i - 1] === 'D',
                // 'bg-green-300': computedReals[ei][i - 1] === 'N'
              }"
            >
              {{ computedReals[ei][i - 1] }}
            </td>
          </tr>
        </template>

        <tr class="bg-orange-100">
          <td
            class="text-center border whitespace-nowrap text-sm font-medium text-gray-800"
          ></td>
          <td
            class="text-center border whitespace-nowrap text-sm font-medium text-gray-800"
          ></td>
          <td
            v-for="i in numberOfDaysInMonth"
            class="border text-center whitespace-nowrap text-sm text-gray-800 p-2"
          >
            <div>
              <div>{{ activeWorking(i, computedShifts) }}</div>
            </div>
          </td>

          <td class="whitespace-nowrap text-end text-sm font-medium"></td>
        </tr>
        <tr v-if="!props.showProvisionalShifts" class="bg-orange-100">
          <td
            class="text-center border whitespace-nowrap text-sm font-medium text-gray-800"
          ></td>
          <td
            class="text-center border whitespace-nowrap text-sm font-medium text-gray-800"
          ></td>
          <td
            v-for="i in numberOfDaysInMonth"
            class="border text-center whitespace-nowrap text-sm text-gray-800 p-2"
            :class="{
              'bg-warning text-black':
                activeWorking(i, computedShifts) !==
                activeRealWorking(i, props.reals),
            }"
          >
            <div>
              <div>{{ activeRealWorking(i, props.reals) }}</div>
            </div>
          </td>

          <td class="whitespace-nowrap text-end text-sm font-medium"></td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style>
.bg-red-100 {
  background-color: #fee2e2;
}

.bg-blue-100 {
  background-color: #dbeafe;
}

.bg-green-100 {
  background-color: #f0fff4;
}

.bg-green-300 {
  background-color: #c6f6d5;
}

.table-sticky th:first-child,
.table-sticky td:first-child {
  position: sticky;
  left: 0;
  background-color: white;
}
/* .table-sticky td:nth-child(2) {
  position: sticky;
  background-color: #dbeafe;
} */
</style>
