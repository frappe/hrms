<script setup lang="ts">
import { ref, computed, defineProps, onMounted } from "vue";
import moment from "moment";

const props = defineProps([
  "shifts",
  "employees",
  "startDate",
  "reals",
  "department",
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

const computedShifts = computed(() => {
  return Array(numberOfEmployees.value)
    .fill(0)
    .map((_, i) => {
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
    switch (a) {
      case "D":
        result += 9;
        break;
      case "N":
        result += 14;
        break;
      default:
        break;
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
            switch (s.type) {
              case "D":
                return 9;
              case "N":
                return 14;
              case "L":
                if (s.shift_type === "D") {
                  return -9;
                } else if (s.shift_type === "N") {
                  return -14;
                } else {
                  return 0;
                }
              default:
                return 0;
            }
          })
          .reduce((a, b) => a + b, 0);
      })
      .reduce((a, b) => a + b, 0);
  });
});

const activeWorking = (index, shift) => {
  let d = 0;
  let n = 0;
  for (const element of shift) {
    const s = element;
    switch (s[index - 1]) {
      case "D":
        d++;
        break;
      case "N":
        n++;
        break;
      default:
        break;
    }
  }
  return `${d}D ${n}N T:${d + n}`;
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
  console.log("fetching .....");
  console.log(props.department);

  //fetch shifts
  //   frappe.db
  //     .get_list("Shift Type", {
  //       filters: { department: props.shiftDeparment },
  //       fields: ["*"],
  //       limit: 0,
  //     })
  //     .then((res) => {
  //       depShifts.value = res;
  //       shiftsMap.value = res.reduce((acc, shift) => {
  //         acc[shift.shift_suffix] = shift;
  //         return acc;
  //       }, {});
  //     });
};
</script>
<template>
  <h2 class="mx-auto text-center py-4">
    {{ moment(startOfMonth).format("MMM YYYY") }}
  </h2>
  <div class="w-100 table-responsive">
    <table class="table table-borderless table-sticky w-auto">
      <thead>
        <tr class="border">
          <th scope="col" class="text-nowrap">Employee Name</th>
          <th scope="col" class="text-nowrap">Monthly hrs</th>
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
            class="px-4"
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
            >
              {{ computedShifts[ei][i - 1] }}
            </td>
          </tr>
          <tr>
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
          <tr>
            <th scope="row" class="text-nowrap border-left"></th>
            <td scope="row" class="text-center"></td>
            <td v-for="i in numberOfDaysInMonth" class="text-center"></td>
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
</style>
