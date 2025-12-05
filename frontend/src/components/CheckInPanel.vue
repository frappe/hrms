<template>
	<div class="flex flex-col bg-white rounded w-full py-6 px-4 border-none">
		<h2 class="text-lg font-bold text-gray-900">
			{{ __("Hey, {0} 👋", [employee?.data?.first_name]) }}
			
		</h2>
		
		<template v-if="settings.data?.allow_employee_checkin_from_mobile_app">
			<div class="font-medium text-sm text-gray-500 mt-1.5" v-if="lastLog">
				<span>{{ __("Last {0} was at {1}", [__(lastLogType), formatTimestamp(lastLog.time)]) }}</span>
				<span class="whitespace-pre"> &middot; </span>
				<router-link :to="{ name: 'EmployeeCheckinListView' }" v-slot="{ navigate }">
					<span @click="navigate" class="underline">View List</span>
				</router-link>
			</div>
			<Button
				class="mt-4 mb-1 drop-shadow-sm py-5 text-base"
				id="open-checkin-modal"
				@click="handleEmployeeCheckin"
			>
				<template #prefix>
					<FeatherIcon
						:name="nextAction.action === 'IN' ? 'arrow-right-circle' : 'arrow-left-circle'"
						class="w-4"
					/>
				</template>
				{{ nextAction.label }}
			</Button>
		</template>

		<div v-else class="font-medium text-sm text-gray-500 mt-1.5">
			{{ dayjs().format("ddd, D MMMM, YYYY") }}
		</div>
	</div>

	<!-- Modal Section -->
	<ion-modal
		v-if="settings.data?.allow_employee_checkin_from_mobile_app"
		ref="modal"
		trigger="open-checkin-modal"
		
		@didPresent="onModalOpen"
		@didDismiss="onModalClose"
	>
	<!-- <ion-modal
  v-if="settings.data?.allow_employee_checkin_from_mobile_app"
  ref="modal"
  trigger="open-checkin-modal"
  @didPresent="onModalOpen"
  @didDismiss="onModalClose"
  class="custom-center-modal"
> -->
		<div class="h-120 w-full flex flex-col items-center justify-center gap-5 p-4 mb-5 top-20">
			<!-- <div class="flex flex-col gap-1.5 mt-2 items-center justify-center">
				<div class="font-medium text-md">
					{{ dayjs(checkinTimestamp).format("hh:mm:ss a") }}
				</div>
				<div class="font-medium text-gray-500 text-sm">
					{{ dayjs().format("D MMM, YYYY") }}
				</div>
			</div> -->

			
			<div class="flex flex-col items-center justify-center gap-4 w-full border border-gray-300 rounded p-4 shadow-xs">
				<!-- <h3 class="text-lg font-semibold">Face Verification</h3> -->

				<div class="flex flex-col md:flex-row gap-6 items-center">
					
					<div class="flex flex-col items-center">
	<!-- <h4 class="font-medium mb-2">Profile Reference</h4> -->

	<!-- <img
		v-if="referenceImageSrc"
		:src="referenceImageSrc"
		alt="Reference"
		class="rounded-lg border border-gray-400 w-40 h-40 object-cover"
	/> -->
	<!-- <img
	v-if="referenceImageSrc"
									
									:src="referenceImageSrc"
									:label="user.data.first_name"
									size="xl"
								/> -->

	<!-- <div v-else class="text-gray-500 italic text-sm">Loading image...</div> -->
</div>

					<!-- <img
							
							:src="employee?.data?.image"
							alt="Reference"
							class="rounded-lg border border-gray-400 w-40 h-40 object-cover"
						/> -->

					
					<div class="flex flex-col items-center">
						<!-- <h4 class="font-medium mb-2">Live Camera</h4> -->
						<video
							ref="video"
							autoplay
							playsinline
							muted
							class="rounded-lg border border-gray-400 bg-black "
						></video>
					</div>
				</div>

				<div class="mt-4 font-semibold text-center" :style="{ color: statusColor }">
					{{ statusMessage }}
				</div>

				<!-- <Button
				v-if="!faceMatched"
					@click="startComparison"
					variant="solid"
				class="w-full py-5 text-sm disabled:bg-gray-700"
					>
					Check Photo
				</Button> -->
			</div>
<div class="w-full grid grid-cols-1 md:grid-cols-2 gap-4">
  <div v-if="field_employee==='Yes' && isCheckOut">
    <label class="form-label text-xs">Type</label>
    <FormControl
      type="autocomplete"
      :options="[
        { label: 'Lead', value: 'Lead' },
        { label: 'Opportunity', value: 'Opportunity' },
        { label: 'Hospital', value: 'Hospital' },
        { label: 'CAR', value: 'CAR' }
      ]"
      size="sm"
      variant="outline"
      placeholder="Select Type"
      v-model="typeofCheckIn"
      :input-class="'bg-gray-100 border border-blue-500 text-gray-800 focus:ring-blue-500 focus:border-blue-600'"
    />
  </div>

  <div v-if="typeofCheckIn?.value === 'Lead'">
    <label class="form-label text-xs" >Lead</label>
    <FormControl
      type="autocomplete"
      :options="leadOptions"
      size="sm"
      variant="outline"
      placeholder="Select Lead"
      v-model="leadValue"
      :input-class="'bg-gray-100 border border-blue-500 text-gray-800 focus:ring-blue-500 focus:border-blue-600'"
    />
  </div>
    


  <div v-if="typeofCheckIn?.value === 'Opportunity'">
    <label class="form-label text-xs" >Opportunity</label>
    <FormControl
      type="autocomplete"
      :options="OpportunityOptions"
      size="sm"
      variant="outline"
      placeholder="Select Opportunity"
      v-model="opportunityValue"
      :input-class="'bg-gray-100 border border-blue-500 text-gray-800 focus:ring-blue-500 focus:border-blue-600'"
    />
  </div>

  <div v-if="typeofCheckIn?.value === 'Hospital'">
    <label class="form-label text-xs" >Hospital</label>
    <FormControl
      type="autocomplete"
      :options="HospitalOptions"
      size="sm"
      variant="outline"
      placeholder="Select Hospital"
      v-model="hospitalValue"
      :input-class="'bg-gray-100 border border-blue-500 text-gray-800 focus:ring-blue-500 focus:border-blue-600'"
    />
  </div>

  <div v-if="typeofCheckIn?.value === 'CAR'">
    <label class="form-label text-xs">CAR</label>
    <FormControl
      type="autocomplete"
      :options="CarOptions"
      size="sm"
      variant="outline"
      placeholder="Select CAR"
      v-model="carValue"
      :input-class="'bg-gray-100 border border-blue-500 text-gray-800 focus:ring-blue-500 focus:border-blue-600'"
    />
  </div>
</div>



			<template v-if="settings.data?.allow_geolocation_tracking">
				<span v-if="locationStatus" class="font-medium text-gray-500 text-sm">
					{{ locationStatus }}
				</span>

				<!-- <div class="rounded border-4 translate-z-0 block overflow-hidden w-full h-170">
					<iframe
						width="100%"
						height="170"
						frameborder="0"
						scrolling="no"
						marginheight="0"
						marginwidth="0"
						style="border: 0"
						:src="`https://maps.google.com/maps?q=${latitude},${longitude}&hl=en&z=15&amp;output=embed`"
					></iframe>
				</div> -->
			</template>
			<Checkbox
			v-if="nextAction.action ==='OUT'"
    size="sm"
    :value="true"
    v-model="forgetCheckOut"
    label="Forget to CheckOut"
  />
  <!-- faceMatched === true &&  -->
			<Button
			v-if="field_employee==='Yes' && isSalesFaceMatched"
				:loading="checkins.insert.loading"
				variant="solid"
				class="w-full py-5 text-sm disabled:bg-gray-700"
				@click="submitLog(nextAction.action)"
			>
				{{ __("Confirm {0}", [nextAction.label]) }}
			</Button>
		</div>
	</ion-modal>

<!-- Create Lead Popup -->
<!-- <div v-if="showLeadModal" class="popup-overlay">
  <div class="popup-container">

    <div class="popup-header">
      <h3 class="text-lg font-semibold">Create Lead</h3>
      <button class="close-btn" @click="showLeadModal = false">×</button>
    </div>

    <div class="popup-body space-y-2">
      <FormControl type="select" v-model="newLead.salutation" :options="['Mr', 'Ms', 'Mrs', 'Dr']" label="Salutation" />
      <FormControl type="text" v-model="newLead.first_name" label="First Name" />
      <FormControl type="text" v-model="newLead.middle_name" label="Middle Name" />
      <FormControl type="text" v-model="newLead.last_name" label="Last Name" />
      <FormControl type="select" v-model="newLead.gender" :options="['Male', 'Female', 'Other']" label="Gender" />
      <FormControl type="text" v-model="newLead.mobile_no" label="Mobile No" />
      <FormControl type="text" v-model="newLead.organization" label="Organization Name" />
    </div>

    <div class="popup-footer">
      <button class="btn-cancel" @click="showLeadModal = false">Cancel</button>
      <button class="btn-save" @click="createLead">Save</button>
    </div>

  </div>
</div> -->

<IonModal :is-open="showLeadModal" @didDismiss="showLeadModal = false" class="lead-modal ios modal-default show-modal">
  <div class="p-4 w-full   ">

    <h2 class="text-lg font-semibold mb-2">Create Lead</h2>

<div class="grid grid-cols-1 md:grid-cols-1 gap-2">

  <div>
    <label class="text-xs font-medium text-gray-700">Salutation</label>
    <select v-model="newLead.salutation"
      class="w-full border border-gray-400 h-8 px-2 rounded text-sm focus:border-gray-600 focus:ring-0">
      <option value="">Select</option>
	  <option>Dr</option>
      <option>Mr</option>
      <option>Ms</option>
      <option>Mrs</option>
      <option>Miss</option>
    </select>
  </div>

  <div>
    <label class="text-xs font-medium text-gray-700">First Name</label>
    <input type="text" v-model="newLead.first_name"
      class="w-full border border-gray-400 h-8 px-2 rounded text-sm focus:border-gray-600 focus:ring-0" />
  </div>

  <!-- <div>
    <label class="text-xs font-medium text-gray-700">Middle Name</label>
    <input type="text" v-model="newLead.middle_name"
      class="w-full border border-gray-400 h-8 px-2 rounded text-sm focus:border-gray-600 focus:ring-0" />
  </div>

  <div>
    <label class="text-xs font-medium text-gray-700">Last Name</label>
    <input type="text" v-model="newLead.last_name"
      class="w-full border border-gray-400 h-8 px-2 rounded text-sm focus:border-gray-600 focus:ring-0" />
  </div>

  <div>
    <label class="text-xs font-medium text-gray-700">Gender</label>
    <select v-model="newLead.gender"
      class="w-full border border-gray-400 h-8 px-2 rounded text-sm focus:border-gray-600 focus:ring-0">
      <option value="">Select</option>
      <option>Male</option>
      <option>Female</option>
      <option>Other</option>
    </select>
  </div> -->

  <div>
    <label class="text-xs font-medium text-gray-700">Mobile No</label>
    <input type="text" v-model="newLead.mobile_no"
      class="w-full border border-gray-400 h-8 px-2 rounded text-sm focus:border-gray-600 focus:ring-0" />
  </div>

  <!-- <div>
    <label class="text-xs font-medium text-gray-700">Organization Name</label>
    <input type="text" v-model="newLead.organization"
      class="w-full border border-gray-400 h-8 px-2 rounded text-sm focus:border-gray-600 focus:ring-0" />
  </div> -->

  <!-- <div>
    <label class="text-xs font-medium text-gray-700">Job Title</label>
    <input type="text" v-model="newLead.job_title"
      class="w-full border border-gray-400 h-8 px-2 rounded text-sm focus:border-gray-600 focus:ring-0" />
  </div>

  <div>
    <label class="text-xs font-medium text-gray-700">Request Type</label>
    <input type="text" v-model="newLead.request_type"
      class="w-full border border-gray-400 h-8 px-2 rounded text-sm focus:border-gray-600 focus:ring-0" />
  </div> -->

</div>




    <div class="flex justify-end gap-3 pt-3">
      <Button 
	  :variant="'outline'"
    :ref_for="true"
    theme="gray"
    size="sm"
	  @click="showLeadModal = false">Cancel</Button>
      <Button :variant="'solid'"
    :ref_for="true"
    theme="gray"
    size="sm"
	 @click="createLead">Save</Button>
    </div>

  </div>
</IonModal>

<IonModal :is-open="showOpportunityModal" @didDismiss="showOpportunityModal = false" class="lead-modal">
  <div class="p-4 w-full h-120px">

    <h2 class="text-lg font-semibold mb-3">Create Opportunity</h2>

    <div class="grid grid-cols-1 md:grid-cols-1 gap-2">

      <div>
        <label class="text-xs font-medium text-gray-700">Lead (Party Name)</label>
        <!-- <input type="text" v-model="newOpportunity.party_name"
          class="w-full border border-gray-400 h-8 px-2 rounded text-sm" /> -->
		 <select
  v-model="newOpportunity.party_name"
  class="w-full border border-gray-400 h-8 px-2 rounded text-sm focus:border-gray-600 focus:ring-0"
>
  <option value="">Select</option>

  <option
    v-for="lead in leadOptions"
    :key="lead.value"
    :value="lead.value"
  >
    {{ lead.label }}
  </option>
</select>

      </div>

      <!-- <div>
        <label class="text-xs font-medium text-gray-700">Opportunity From</label>
        <input type="text" v-model="newOpportunity.opportunity_from"
          class="w-full border border-gray-400 h-8 px-2 rounded text-sm" />
      </div> -->

      <!-- <div>
        <label class="text-xs font-medium text-gray-700">Opportunity Type</label>
        <input type="text" v-model="newOpportunity.opportunity_type"
          class="w-full border border-gray-400 h-8 px-2 rounded text-sm" />
      </div>

      <div>
        <label class="text-xs font-medium text-gray-700">Source</label>
        <input type="text" v-model="newOpportunity.source"
          class="w-full border border-gray-400 h-8 px-2 rounded text-sm" />
      </div> -->

      <!-- <div>
        <label class="text-xs font-medium text-gray-700">Opportunity Owner</label>
        <input type="text" v-model="newOpportunity.opportunity_owner"
          class="w-full border border-gray-400 h-8 px-2 rounded text-sm" />
      </div>

      <div>
        <label class="text-xs font-medium text-gray-700">Sales Stage</label>
        <input type="text" v-model="newOpportunity.sales_stage"
          class="w-full border border-gray-400 h-8 px-2 rounded text-sm" />
      </div> -->

      <div>
        <label class="text-xs font-medium text-gray-700">Expected Closing</label>
        <input type="date" v-model="newOpportunity.expected_closing"
          class="w-full border border-gray-400 h-8 px-2 rounded text-sm" />
      </div>

      <div>
        <label class="text-xs font-medium text-gray-700">Probability (%)</label>
        <input type="number" v-model="newOpportunity.probability"
          class="w-full border border-gray-400 h-8 px-2 rounded text-sm" />
      </div>

      <div>
        <label class="text-xs font-medium text-gray-700">Opportunity Amount</label>
        <input type="number" v-model="newOpportunity.opportunity_amount"
          class="w-full border border-gray-400 h-8 px-2 rounded text-sm" />
      </div>

    </div>

    <div class="flex justify-end gap-3 pt-3">
      <Button size="sm" variant="outline" @click="showOpportunityModal = false">Cancel</Button>
      <Button size="sm" variant="solid" @click="createOpportunity">Save</Button>
    </div>

  </div>
</IonModal>

<!-- <IonModal :is-open="showHospitalModal" @didDismiss="showHospitalModal = false" class="lead-modal">
  <div class="p-4 w-full">

    <h2 class="text-lg font-semibold mb-3">Create Hospital</h2>

    <div class="grid grid-cols-1 md:grid-cols-1 gap-2">

      <div>
        <label class="text-xs font-medium text-gray-700">Hospital Name</label>
        <input type="text" v-model="newHospital.hospital_name"
          class="w-full border border-gray-400 h-8 px-2 rounded text-sm" />
      </div>

      <div>
        <label class="text-xs font-medium text-gray-700">Contact Number</label>
        <input type="text" v-model="newHospital.contact_number"
          class="w-full border border-gray-400 h-8 px-2 rounded text-sm" />
      </div>

      <div>
        <label class="text-xs font-medium text-gray-700">Address</label>
        <input type="text" v-model="newHospital.address"
          class="w-full border border-gray-400 h-8 px-2 rounded text-sm" />
      </div>

      <div>
        <label class="text-xs font-medium text-gray-700">Email</label>
        <input type="email" v-model="newHospital.email"
          class="w-full border border-gray-400 h-8 px-2 rounded text-sm" />
      </div>

    </div>

    <div class="flex justify-end gap-3 pt-3">
      <Button size="sm" variant="outline" @click="showHospitalModal = false">Cancel</Button>
      <Button size="sm" variant="solid" @click="createHospital">Save</Button>
    </div>

  </div>
</IonModal> -->


</template>

<script setup>
import { createResource, createListResource, toast, FeatherIcon,Avatar,Autocomplete,FormControl,Checkbox } from "frappe-ui"
import { computed, inject, ref, onMounted, onBeforeUnmount, reactive, watch } from "vue"
import { IonModal,IonButton, modalController } from "@ionic/vue"
import { formatTimestamp } from "@/utils/formatters"
import * as faceapi from "face-api.js"
import FingerprintJS from "@fingerprintjs/fingerprintjs";


const video = ref(null)
const referenceImageSrc = ref(null)
const referenceDescriptor = ref(null)
const statusMessage = ref("Initializing...")

let faceMatched = false
let isCheckOut = false
let isSalesFaceMatched=false

const statusColor = ref("gray")
let modelsLoaded = false
let comparisonInterval = null
let locations = ref([])
let stream = null
let field_employee=ref("")
let device_id=ref("")
let locationDescription=ref("")


// let typeofCheckIn=ref("")
let typeofCheckIn = ref(null)
let carValue=ref(null)
let leadValue=ref(null)
let opportunityValue=ref(null)
let hospitalValue=ref(null)
let CarOptions=ref([])
let leadOptions=ref([])
let HospitalOptions=ref([])
let OpportunityOptions=ref([])

let lastLogRefDoctype=ref(null)
let lastLogRefName=ref(null)

let currentLogRefDoctype=ref(null)
let currentLogRefName=ref(null)
let currentCheckINID=ref(null)
let lastCheckOutID=ref(null)


const DOCTYPE = "Employee Checkin"
const socket = inject("$socket")
const employee = inject("$employee")
const user = inject("$user")
const dayjs = inject("$dayjs")
const __ = inject("$translate")
const wfh =inject("$wfh")
const geofence =inject ("$geofence")
const location =inject("$location")
const leads =inject("$leads")



const checkinTimestamp = ref(null)
const latitude = ref(0)
const longitude = ref(0)
const locationStatus = ref("")
const loginlocation = ref("")

const showLeadModal = ref(false);
const forgetCheckOut = ref(false);

const newLead = reactive({
  salutation: "",
  first_name: "",
//   middle_name: "",
//   last_name: "",
//   gender: "",
  mobile_no: "",
//   organization: "",
//   request_type:"",
// job_title:""
});
const showOpportunityModal = ref(false);
const showHospitalModal = ref(false);

const newOpportunity = reactive({
  party_name: "",
  opportunity_from: "Lead",
  opportunity_type: "",
//   source: "",
  opportunity_owner: "",
//   sales_stage: "",
  expected_closing: "",
  probability: "",
  opportunity_amount: "",
});

const newHospital = reactive({
  hospital_name: "",
  contact_number: "",
  address: "",
  email: "",
});

async function createLead() {
  const csrfToken =
    frappe?.csrf_token || window?.csrf_token || getCookie("csrf_token");

  const payload = {
    first_name: newLead.first_name,
    mobile_no: newLead.mobile_no,
	salutation:newLead.salutation
  };

  const response = await fetch(
    "/api/method/hrms.api.api.create_lead",
    {
      method: "POST",
      credentials: "include", //  send session cookies
      headers: {
        "Content-Type": "application/json",
        "X-Frappe-CSRF-Token": csrfToken, //  required for POST/PUT/DELETE
      },
      body: JSON.stringify(payload),
    }
  );

  const result = await response.json();

  if (result.message) {
	const createdLead = result.message.data; 
    // console.log(" Lead Created:", result.message);
    // Optional: Clear form
    newLead.first_name = "";
    newLead.mobile_no = "";
	newLead.salutation="";
	showLeadModal.value=false;
	
	  // Push new Lead into Autocomplete options
  const newOption = {
    label:`${createdLead.name} (${createdLead.first_name}, ${createdLead.mobile_no})`,
    value: createdLead.name,
  };
  leadOptions.value = [newOption, ...leadOptions.value];

  // Set selected Lead
  leadValue.value = newOption;

  console.log("✅ New Lead Selected:", leadValue.value);

  } else {
    console.error(" Error Creating Lead:", result);
  }
}

async function createOpportunity() {
  const csrfToken =
    frappe?.csrf_token || window?.csrf_token || getCookie("csrf_token");

  const payload = {
    party_name: newOpportunity.party_name,
	opportunity_from:"Lead",
	opportunity_owner:'',
    expected_closing: newOpportunity.expected_closing,
    opportunity_amount: newOpportunity.opportunity_amount,
	probability:newOpportunity.probability
  };

  const response = await fetch(
    "/api/method/hrms.api.api.create_opportunity",
    {
      method: "POST",
      credentials: "include", //  send session cookies
      headers: {
        "Content-Type": "application/json",
        "X-Frappe-CSRF-Token": csrfToken, //  required for POST/PUT/DELETE
      },
      body: JSON.stringify(payload),
    }
  );

  const result = await response.json();

  if (result.message) {
	const newOpportunityRes = result.message.data; 
    // console.log(" Lead Created:", result.message);
    // Optional: Clear form

	
	  // Push new Lead into Autocomplete options
  const newOption = {
    label:`${newOpportunityRes.name} (${newOpportunityRes.opportunity_from}, ${newOpportunityRes.party_name})`,
    value: newOpportunityRes.name,
  };
  OpportunityOptions.value = [newOption, ...OpportunityOptions.value ];

  // Set selected Lead
  opportunityValue.value = newOption;

  console.log("New opportunity Selected:", opportunityValue.value);
    newOpportunity.party_name = "";
    newOpportunity.opportunity_from = "Lead";
	newOpportunity.opportunity_owner="";
	newOpportunity.expected_closing="";
	newOpportunity.opportunity_amount="";
	newOpportunity.probability="";
	
	showOpportunityModal.value = false;

  } else {
    console.error(" Error Creating Opportunity:", result);
  }
}





async function createHospital() {
  // API Create call here
  console.log("Create Hospital:", newHospital);
  showHospitalModal.value = false;
}


const settings = createResource({
	url: "hrms.api.get_hr_settings",
	auto: true,
})


const checkins = createListResource({
	doctype: DOCTYPE,
	fields: ["name", "employee", "employee_name", "log_type", "time", "device_id","location","latitude","longitude","reference_dt","reference_dn"],
	filters: { employee: employee.data.name },
	orderBy: "time desc",
})
checkins.reload()

const lastLog = computed(() => {
	if (checkins.list.loading || !checkins.data) return {}
	return checkins.data[0]
})

const lastLogType = computed(() => {
	return lastLog?.value?.log_type === "IN" ? "check-in" : "check-out"
})

const nextAction = computed(() => {
	return lastLog?.value?.log_type === "IN"
		? { action: "OUT", label: __("Check Out") }
		: { action: "IN", label: __("Check In") }
})

function handleLocationSuccess(position) {
	latitude.value = position.coords.latitude
	longitude.value = position.coords.longitude

	locationStatus.value = [
		__("Latitude: {0}°", [Number(latitude.value).toFixed(5)]),
		__("Longitude: {0}°", [Number(longitude.value).toFixed(5)]),
	].join(", ")

	getLocationAPI(latitude.value,longitude.value);
}

function handleLocationError(error) {
	locationStatus.value = "Unable to retrieve your location"
	if (error) locationStatus.value += `: ERROR(${error.code}): ${error.message}`
}

const fetchLocation = () => {
	if (!navigator.geolocation) {
		locationStatus.value = __("Geolocation is not supported by your browser")
	} else {
		locationStatus.value = __("Locating...")
		navigator.geolocation.getCurrentPosition(handleLocationSuccess, handleLocationError)
	}
}

const handleEmployeeCheckin = () => {
	checkinTimestamp.value = dayjs().format("YYYY-MM-DD HH:mm:ss")
	if (settings.data?.allow_geolocation_tracking) fetchLocation()
}

// ✅ Start camera only when popup opens
async function onModalOpen() {
	await loadModels()
	console.log("Empolyee",employee)
	console.log("User",user)
	console.log("Wfh",wfh)
	console.log("Geofence",geofence)
	

	
	// Load employee's image automatically
if (user?.data?.user_image) {
	referenceImageSrc.value = user.data.user_image
	// user.data.image.startsWith("http")
	// 	? user.data.image
	// 	: `${window.location.origin}${user.data.image}`;

	const img = new Image();
	img.crossOrigin = "anonymous";
	img.src = referenceImageSrc.value;

	img.onload = async () => {
		const detection = await faceapi
			.detectSingleFace(img, new faceapi.TinyFaceDetectorOptions())
			.withFaceLandmarks()
			.withFaceDescriptor();

		if (detection) {
			referenceDescriptor.value = detection.descriptor; // img map
			statusMessage.value = "Profile image ready for verification!";
			statusColor.value = "blue";
		} else {
			statusMessage.value = "No face detected in profile image.";
			statusColor.value = "red";
		}
	};
} else {
	statusMessage.value = "";
	// console.log("No profile image found!")
	statusColor.value = "red";
}

	await startCamera()
	statusMessage.value = "" //Camera ready. Upload reference image.
	statusColor.value = "green"

	await startComparison();
}

// 🧹 Stop camera when popup closes
function onModalClose() {
	stopCamera()
	statusMessage.value = "Camera stopped."
	statusColor.value = "gray"
}

async function startCamera() {
	try {
		stream = await navigator.mediaDevices.getUserMedia({ video: true })
		video.value.srcObject = stream
	} catch (err) {
		console.error("Camera access error:", err)
		statusMessage.value = "Camera blocked or unavailable"
		statusColor.value = "red"
	}
}

function stopCamera() {
	if (stream) {
		stream.getTracks().forEach((track) => track.stop())
		stream = null
	}
}

async function loadModels() {
	if (modelsLoaded) return
	const MODEL_URL = "/assets/hrms/models"
	await Promise.all([
		faceapi.nets.tinyFaceDetector.loadFromUri(MODEL_URL),
		faceapi.nets.faceLandmark68Net.loadFromUri(MODEL_URL),
		faceapi.nets.faceRecognitionNet.loadFromUri(MODEL_URL),
		

	])
	modelsLoaded = true
}

// async function loadReferenceImage(event) {
// 	const file = event.target.files[0]
// 	if (!file) return
// 	referenceImageSrc.value = URL.createObjectURL(file)

// 	const img = await faceapi.bufferToImage(file)
// 	const detection = await faceapi
// 		.detectSingleFace(img, new faceapi.TinyFaceDetectorOptions())
// 		.withFaceLandmarks()
// 		.withFaceDescriptor()

// 	if (!detection) {
// 		statusMessage.value = "No face detected in reference image"
// 		statusColor.value = "red"
// 		referenceDescriptor.value = null
// 	} else {
// 		referenceDescriptor.value = detection.descriptor
// 		statusMessage.value = "Reference face ready!"
// 		statusColor.value = "blue"
// 	}
// }

async function startComparison() {
	if (!modelsLoaded) {
		statusMessage.value = "Models not loaded!"
		statusColor.value = "red"
		return
	}
	if (!referenceDescriptor.value) {
		statusMessage.value = "Employee Photo is Missing, Please Contact your HR or Update the Photo in Octa"
		statusColor.value = "red"
		return
	}

	statusMessage.value = "Comparing live face..."
	statusColor.value = "orange"

	if (comparisonInterval) clearInterval(comparisonInterval)
	let blinkDetected = false;
let turnLeftDetected = false;
let turnRightDetected = false;

const BLINK_THRESHOLD = 0.27;

comparisonInterval = setInterval(async () => {

const detection = await faceapi
  .detectSingleFace(video.value, new faceapi.TinyFaceDetectorOptions())
  .withFaceLandmarks()
  .withFaceDescriptor()

if (!detection) {
  statusMessage.value = "No face in camera!"
  statusColor.value = "gray"
  faceMatched = false
  return
}

// 1️⃣ Blink Check
const ear = getEAR(detection.landmarks)
if (!blinkDetected) {
  if (ear < BLINK_THRESHOLD) {
    blinkDetected = true
	
    statusMessage.value = "Blink detected"
    statusColor.value = "green"
  } else {
    statusMessage.value = "Please BLINK 👀"
    statusColor.value = "orange"
    return
  }
}

// 2️⃣ Head Turn Check
// const headTurn = getHeadTurn(detection.landmarks)
// console.log(headTurn);

// if (!turnLeftDetected) {
//   if (headTurn < -1) { // Turn Left
//     turnLeftDetected = true
//     statusMessage.value = "Left turn detected ✅ Now turn head RIGHT"
//     statusColor.value = "green"
//   } else {
//     statusMessage.value = "Turn your head LEFT ⬅️"
//     statusColor.value = "orange"
//     return
//   }
// }

// if (!turnRightDetected) {
//   if (headTurn > 1) { // Turn Right
//     turnRightDetected = true
//     statusMessage.value = "Right turn detected ✅ Verification in progress..."
//     statusColor.value = "green"
//   } else {
//     statusMessage.value = "Turn your head RIGHT ➡️"
//     statusColor.value = "orange"
//     return
//   }
// }

// 3️⃣ Only after real movement → Compare Face
const distance = faceapi.euclideanDistance(referenceDescriptor.value, detection.descriptor)

// if (distance < 0.45) {
// //   faceMatched = true
// //   statusMessage.value = `✅ Face Matched (distance: ${distance.toFixed(3)})`
// //   statusColor.value = "green"
//   console.log("User",user)
    
//     console.log("Geofence",geofence.data)
//     const user_id=user.data.name
//     console.log("User ID",user_id)
//     const geofenceID=geofence.data[0].name
//     console.log("geofenceID",geofenceID)

// 	console.log("WFH", wfh);

// const today = new Date().toISOString().split("T")[0]; // "YYYY-MM-DD"

// const wfhRecordForToday = wfh.data.find(item => item.date === today);

// if (wfhRecordForToday) {
// 	const wfh_user_id = wfhRecordForToday.user;

// 	if (user_id === wfh_user_id) {
// 		faceMatched = true;
// 		statusMessage.value = "Face Matched";
// 		statusColor.value = "green"
// 	}
// }
// else if (user_id === geofenceID) {
 
//     // 1) Face match was already confirmed before this block
//     let insideAnyFence = false;
 
//     const allowedLocations = geofence.data[0].locations; // [{ location: "Main Office"}, { location: "Marathalli"}]
//     const userLat = parseFloat(latitude.value);
//     const userLon = parseFloat(longitude.value);
 
//     console.log("Allowed Locations:", allowedLocations);
//     console.log("All Location Coordinates:", locations.value);
//     console.log("User Lat:", userLat, "User Lon:", userLon);
 
//     for (const loc of allowedLocations) {
//         const locationName = loc.location; // ✅ Correct extraction
//         const center = locations.value.find(l => l.name === locationName);
//             console.log("Center",center);
 
//         if (!center) {
//             console.warn(`No coordinate data for location: ${locationName}`);
//             continue;
//         }
 
//         const centerLat = parseFloat(center.latitude);
//         const centerLon = parseFloat(center.longitude);
//         const radius = parseFloat(center.radius);
 
//         const distance = getDistanceFromLatLonInMeters(
//             userLat,
//             userLon,
//             centerLat,
//             centerLon
//         );
// 		loginlocation.value=center.name
// 		console.log("Login Location",loginlocation.value)
//         // console.log(`→ ${center.name}: Distance = ${distance.toFixed(2)}m | Radius = ${radius}m`);
 
//         if (distance <= radius) {
//             insideAnyFence = true;
//             break; // ✅ Stop after first match
//         }
//     }
 
//     // ✅ FINAL DECISION (DO NOT OVERWRITE)
//     if (insideAnyFence) {
//         faceMatched = true;
//         statusMessage.value = "Face Matched & Inside Allowed Location";
// 		statusColor.value = "green"
		
		
		
// 		// console.log("Checkin Log",lastLog.value);
//     } else {
//         faceMatched = false;
//         statusMessage.value = "Face Matched But You Are Outside the Boundary";
// 		statusColor.value = "red"
//     }
 
// } else {
 
//     // Face not matched case
//     faceMatched = false;
//     statusMessage.value = "Face Not Matched";
// 	statusColor.value = "red"
// }
// } else {
//   faceMatched = false
//   statusMessage.value = `Not Matched (distance: ${distance.toFixed(3)})`
//   statusColor.value = "red"
// }

if (distance < 0.45) {
	isSalesFaceMatched=true
	// statusMessage.value = "Face Matched";
	// 	statusColor.value = "green";

	// console.log("User", user);
	// const user_id = user.data.name;

	// console.log("WFH", wfh);
	// const today = new Date().toISOString().split("T")[0];

	// const wfhRecordForToday = wfh.data.find(item => item.date === today);

	// // ------------------ WFH CASE ------------------
	// if (wfhRecordForToday && user_id === wfhRecordForToday.user && field_employee.value !='Yes') {

	// 	faceMatched = true;
	// 	statusMessage.value = "Face Matched (WFH)";
	// 	statusColor.value = "green";

	// 	// ✅ If IN - directly submit
	// 	if (nextAction.value.action === "IN") {
	// 		submitLog(nextAction.value.action);
	// 	} 
	// 	else {
	// 		// ✅ OUT → verify boundary using last check-in coordinates
	// 		const lastLat = parseFloat(lastLog.value.latitude);
	// 		const lastLon = parseFloat(lastLog.value.longitude);
	// 		const defaultRadius = 50;

	// 		const dist = getDistanceFromLatLonInMeters(
	// 			latitude.value, 
	// 			longitude.value, 
	// 			lastLat, 
	// 			lastLon
	// 		);

	// 		if (dist <= defaultRadius) {
	// 			submitLog(nextAction.value.action);
	// 		} else {
	// 			statusMessage.value = "You Are Outside The Work-From-Home Allowed Boundary";
	// 			statusColor.value = "red";
	// 		}
	// 	}
	// 	return; // ✅ Stop here (no geofence check needed)
	// }

	// console.log("WFH", wfh);

const today = new Date().toISOString().split("T")[0];

// ✅ Find WFH record for the logged-in employee that includes today in choose_date
const wfhRecordForToday = wfh.data.find(item => {
  // Check if this record belongs to the same employee
  const sameEmployee = item.employee_wfh_details?.some(
    detail => detail.employee === employee.data.name
  );

  // Check if today's date is one of the chosen WFH dates
  const hasTodayDate = item.choose_date?.some(
    dateItem => dateItem.date === today
  );

  return sameEmployee && hasTodayDate;
});

// ------------------ WFH CASE ------------------
if (wfhRecordForToday && field_employee.value !== "Yes") {
  faceMatched = true;
  statusMessage.value = "Face Matched (WFH)";
  statusColor.value = "green";

  // ✅ If IN - directly submit
  if (nextAction.value.action === "IN") {
    submitLog(nextAction.value.action);
  } else {
    // ✅ OUT → verify boundary using last check-in coordinates
    const lastLat = parseFloat(lastLog.value.latitude);
    const lastLon = parseFloat(lastLog.value.longitude);
    const defaultRadius = 50;

    const dist = getDistanceFromLatLonInMeters(
      latitude.value,
      longitude.value,
      lastLat,
      lastLon
    );

    if (dist <= defaultRadius) {
      submitLog(nextAction.value.action);
    } else {
      statusMessage.value =
        "You Are Outside The Work-From-Home Allowed Boundary";
      statusColor.value = "red";
    }
  }

  return; // ✅ Stop here (no geofence check needed)
}


	// if(field_employee.value !='Yes'){
	// 	// ------------------ OFFICE GEOFENCE CASE ------------------
	// const allowedLocations = geofence.data[0].locations;
	// let insideAnyFence = false;

	// for (const loc of allowedLocations) {
	// 	const center = locations.value.find(l => l.name === loc.location);
	// 	if (!center) continue;

	// 	const distanceToCenter = getDistanceFromLatLonInMeters(
	// 		latitude.value,
	// 		longitude.value,
	// 		center.latitude,
	// 		center.longitude
	// 	);

	// 	if (distanceToCenter <= center.radius) {
	// 		insideAnyFence = true;
	// 		loginlocation.value = center.name;
	// 		break;
	// 	}
	// }

	// if (insideAnyFence) {
	// 	faceMatched = true;
	// 	statusMessage.value = "Face Matched & Inside Allowed Location";
	// 	statusColor.value = "green";

	// 	if (nextAction.value.action === "IN") {
	// 		locationDescription.value='';
	// 		submitLog(nextAction.value.action);
			
	// 	} else {
	// 		locationDescription.value='';
	// 		// ✅ OUT → verify using last check-in location
	// 		const checkinCenter = locations.value.find(l => l.name === lastLog.value.location);
	// 		if (!checkinCenter) {
	// 			statusMessage.value = "Previous check-in location not found";
	// 			statusColor.value = "red";
	// 			return;
	// 		}

	// 		const distanceToLastCenter = getDistanceFromLatLonInMeters(
	// 			latitude.value,
	// 			longitude.value,
	// 			checkinCenter.latitude,
	// 			checkinCenter.longitude
	// 		);

	// 		if (distanceToLastCenter <= checkinCenter.radius) {
	// 			submitLog(nextAction.value.action);
	// 		} else {
	// 			statusMessage.value = "You Are Outside the Boundary";
	// 			statusColor.value = "red";
	// 		}
	// 	}
	// } else {
	// 	faceMatched = false;
	// 	statusMessage.value = "Matched but Outside Allowed Office Boundary";
	// 	statusColor.value = "red";
	// }
	
	// } 


	if (field_employee.value !== 'Yes') {
  // ------------------ OFFICE GEOFENCE CASE ------------------
  const allowedFences = geofence.data[0]?.fence || [];
  let insideAnyFence = false;

  for (const loc of allowedFences) {
    const distanceToCenter = getDistanceFromLatLonInMeters(
      latitude.value,
      longitude.value,
      parseFloat(loc.latitude),
      parseFloat(loc.longitude)
    );

    if (distanceToCenter <= loc.radius) {
      insideAnyFence = true;
      loginlocation.value = loc.location; // store current matched location name
      break;
    }
  }

  if (insideAnyFence) {
    faceMatched = true;
    statusMessage.value = "Face Matched & Inside Allowed Location";
    statusColor.value = "green";

    if (nextAction.value.action === "IN") {
      locationDescription.value = '';
      submitLog(nextAction.value.action);
    } else {
      locationDescription.value = '';

      // ✅ OUT → verify boundary using last check-in coordinates
      const lastLat = parseFloat(lastLog.value.latitude);
      const lastLon = parseFloat(lastLog.value.longitude);
      const lastRadius = lastLog.value.radius ? parseFloat(lastLog.value.radius) : 50;

      const distanceToLastCenter = getDistanceFromLatLonInMeters(
        latitude.value,
        longitude.value,
        lastLat,
        lastLon
      );

      if (distanceToLastCenter <= lastRadius) {
        submitLog(nextAction.value.action);
      } else {
        statusMessage.value = "You Are Outside the Boundary";
        statusColor.value = "red";
      }
    }
  } else {
    faceMatched = false;
    statusMessage.value = "Matched but Outside Allowed Office Boundary";
    statusColor.value = "red";
  }
}



	// sales emp
	else{ 
		if (nextAction.value.action === "IN") {
			// submitLog(nextAction.value.action);
			statusMessage.value = "Face Matched"
    		statusColor.value = "green"
			faceMatched = true;
			isCheckOut=true;
			console.log("Last Log",lastLog.value);
			lastLogRefDoctype.value=lastLog.value.reference_dt
			lastLogRefName.value=lastLog.value.reference_dn
			lastCheckOutID.value=lastLog.value.name;
			// console.log("last --",lastLogRefDoctype.value)
		}else{
			isCheckOut=false;
			// faceMatched = true;
			// ✅ OUT → verify boundary using last check-in coordinates
			console.log("Last Log",lastLog.value);
			lastLogRefDoctype.value=lastLog.value.reference_dt
			lastLogRefName.value=lastLog.value.reference_dn
			lastCheckOutID.value=lastLog.value.name;
			// console.log("last --",lastLogRefDoctype.value)

			const lastLat = parseFloat(lastLog.value.latitude);
			const lastLon = parseFloat(lastLog.value.longitude);
			const defaultRadius = 50;

			const dist = getDistanceFromLatLonInMeters(
				latitude.value, 
				longitude.value, 
				lastLat, 
				lastLon
			);

			if (dist <= defaultRadius) {
				submitLog(nextAction.value.action);

			} else {
				statusMessage.value = "You Are Outside The  Allowed Boundary";
				statusColor.value = "red";
			}
		}
		}

} else {
	faceMatched = false;
	statusMessage.value = `Not Matched (distance: ${distance.toFixed(3)})`;
	statusColor.value = "red";
}



}, 1000)

}
function getDistanceFromLatLonInMeters(lat1, lon1, lat2, lon2) {
    const R = 6371e3; // meters
    const φ1 = lat1 * Math.PI/180;
    const φ2 = lat2 * Math.PI/180;
    const Δφ = (lat2-lat1) * Math.PI/180;
    const Δλ = (lon2-lon1) * Math.PI/180;
 
    const a = Math.sin(Δφ/2) ** 2 +
        Math.cos(φ1) * Math.cos(φ2) *
        Math.sin(Δλ/2) ** 2;
 
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c; // in meters
}
// function getDistanceFromLatLonInMeters(lat1, lon1, lat2, lon2) {
//     const R = 6371e3; // meters
//     const φ1 = lat1 * Math.PI/180;
//     const φ2 = lat2 * Math.PI/180;
//     const Δφ = (lat2-lat1) * Math.PI/180;
//     const Δλ = (lon2-lon1) * Math.PI/180;
 
//     const a = Math.sin(Δφ/2) ** 2 +
//         Math.cos(φ1) * Math.cos(φ2) *
//         Math.sin(Δλ/2) ** 2;
 
//     const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
//     return R * c; // in meters
// }

function getEAR(landmarks) {
	const left = landmarks.getLeftEye().map(pt => [pt.x, pt.y])
	const right = landmarks.getRightEye().map(pt => [pt.x, pt.y])

	function ear(eye) {
		const A = faceapi.euclideanDistance(eye[1], eye[5])
		const B = faceapi.euclideanDistance(eye[2], eye[4])
		const C = faceapi.euclideanDistance(eye[0], eye[3])
		return (A + B) / (2.0 * C)
	}

	return (ear(left) + ear(right)) / 2.0
}

function getHeadTurn(landmarks) {
  const nose = landmarks.getNose();
  const leftEye = landmarks.getLeftEye();
  const rightEye = landmarks.getRightEye();

  const noseX = nose[3].x;
  const eyeCenter = (leftEye[0].x + rightEye[3].x) / 2;

  return noseX - eyeCenter; // positive → right turn, negative → left turn
}


function captureImage() {
	const canvas = document.createElement("canvas")
	canvas.width = video.value.videoWidth
	canvas.height = video.value.videoHeight
	const ctx = canvas.getContext("2d")
	ctx.drawImage(video.value, 0, 0, canvas.width, canvas.height)
	return canvas.toDataURL("image/jpeg", 0.9) // returns Base64 image
}

async function getDistanceInMeters(currentLat, currentLon, expectedLat, expectedLon) {
  const key = import.meta.env.VITE_AZURE_MAPS_KEY; // <-- Replace only this

//   expectedLat = 12.8742
//   expectedLon= 77.5569

  const url = `https://atlas.microsoft.com/route/directions/json?api-version=1.0&subscription-key=${key}&query=${currentLat},${currentLon}:${expectedLat},${expectedLon}`;

  try {
    const response = await fetch(url);
    const data = await response.json();

    const distance = data?.routes?.[0]?.summary?.lengthInMeters;

    if (!distance && distance !== 0) {
    //   console.error("Invalid Distance Response:", data);
      return 0;
    }

    // console.log("✅ Distance (meters):", distance);
    return distance;
  } catch (err) {
    console.error("Azure Distance API Error:", err);
    return null;
  }
}

async function getLocationAPI(currentLat, currentLon) {
  const key = import.meta.env.VITE_AZURE_MAPS_KEY; // <-- Replace only this

//   expectedLat = 12.8742
//   expectedLon= 77.5569

  const url = `https://atlas.microsoft.com/search/address/reverse/json?api-version=1.0&subscription-key=${key}&query=${currentLat},${currentLon}`;

  try {
    const response = await fetch(url);
    const data = await response.json();

    // const distance = data?.routes?.[0]?.summary?.lengthInMeters;

    // if (!distance && distance !== 0) {
    //   console.error("Invalid Distance Response:", data);
    //   return null;
    // }

    // console.log("Location Data :", data.addresses[0].address.freeformAddress);
	locationDescription.value=data.addresses[0].address.freeformAddress;
	console.log("Location Description",locationDescription.value);
    
  } catch (err) {
    console.error("Azure Distance API Error:", err);
    
  }
}
async function CreateCheckInJoureny(){
	
	console.log("Expected",lastLog.value.latitude,",",lastLog.value.longitude)
	console.log("Current",latitude.value,",",longitude.value)
	 
	const distance = await getDistanceInMeters(
    latitude.value,
    longitude.value,
    lastLog.value.latitude,
    lastLog.value.longitude
  );
  const dis_km=0
  if(distance!==0){
dis_km = Number((distance / 1000).toFixed(2));
  }

   

console.log("Distance",dis_km);


// -----------------
			console.log("last chek --",lastLogRefDoctype.value)
			console.log("Current chek --",currentLogRefDoctype.value)


// const refDocDT = typeofCheckIn.value?.value || lastLogRefDoctype.value || "";
// const refDocDN =
//   hospitalValue.value?.value ||
//   carValue.value?.value ||
//   leadValue.value?.value ||
//   opportunityValue.value?.value || lastLogRefName.value ||
//   "";
// console.log("Reference DocType:", refDocDT);
// console.log("Reference DocName:", refDocDN);
const lastLogID=lastLog.value.name
console.log("Last Log ID :", lastLogID);

const employeeData=employee.data
const now = new Date();
const formattedDateTime =
now.getFullYear() + '-' +
(now.getMonth() + 1).toString().padStart(2, '0') + '-' +
now.getDate().toString().padStart(2, '0'); 

const csrfToken =
    frappe?.csrf_token || window?.csrf_token || getCookie("csrf_token");

  const payload = {
    employee: employeeData.name,
	user:employeeData.user_id,
	checkout:lastCheckOutID.value,
	checkout_reference:lastLogRefDoctype.value,
	checkout_reference_name:lastLogRefName.value,
	checkin:currentCheckINID.value,
	checkin_reference:currentLogRefDoctype.value,
	checkin_reference_name:currentLogRefName.value,
	// reference_dt:refDocDT,
	// reference_name:refDocDN,
    distance: dis_km,
    date: formattedDateTime,
	// description:locationDescription.value
  };

  const response = await fetch(
    "/api/method/hrms.api.api.create_checkin_joureny",
    {
      method: "POST",
      credentials: "include", //  send session cookies
      headers: {
        "Content-Type": "application/json",
        "X-Frappe-CSRF-Token": csrfToken, //  required for POST/PUT/DELETE
      },
      body: JSON.stringify(payload),
    }
  );

  const result = await response.json();

  if (result.message) {
	console.log("result",result.message.data);
	

  } else {
    console.error(" Error Creating CheckIn Joureny:", result);
  }


}

const submitLog = (logType) => {
	const actionLabel = logType === "IN" ? __("Check-in") : __("Check-out")
	console.log(actionLabel);
	
const refDocDT = typeofCheckIn.value?.value || lastLogRefDoctype.value || "";
const refDocDN =
  hospitalValue.value?.value ||
  carValue.value?.value ||
  leadValue.value?.value ||
  opportunityValue.value?.value || lastLogRefName.value ||
  "";
console.log("Reference DocType:", refDocDT);
console.log("Reference DocName:", refDocDN);

currentLogRefDoctype.value=refDocDT
currentLogRefName.value=refDocDN

	const capturedImage = captureImage()
	checkins.insert.submit(
		{
			employee: employee.data.name,
			log_type: logType,
			time: checkinTimestamp.value,
			latitude: latitude.value,
			longitude: longitude.value,
			location:loginlocation.value,
			device_id:device_id.value,
			reference_dt: refDocDT,   // ← fixed
  			reference_dn: refDocDN ,   // ← fixed
			description:locationDescription.value
		},
		{
		async onSuccess(doc) {
			const checkinId = doc.name
			console.log("ID",checkinId);
			currentCheckINID.value=checkinId;
				if (capturedImage) {
					await uploadCapturedImage(doc.name, capturedImage)
				}
				modalController.dismiss()
				stopCamera()
				if (field_employee.value === 'Yes' && actionLabel === 'Check-in') {

						const now = new Date();

						const formattedDateTime =
						now.getFullYear() + '-' +
						(now.getMonth() + 1).toString().padStart(2, '0') + '-' +
						now.getDate().toString().padStart(2, '0'); 
						


						console.log("Current Date-Time:", formattedDateTime);
			console.log("last --",lastLogRefDoctype.value)

						const lastDate = lastLog.value.time.split(" ")[0];
						console.log("Last Time", lastDate);
						if(lastDate===formattedDateTime){
							CreateCheckInJoureny();
						}

						
					}

				toast({
					title: __("Success"),
					text: __("{0} successful!", [actionLabel]),
					icon: "check-circle",
					position: "bottom-center",
					iconClasses: "text-green-500",
				})
				leadValue.value='',
				hospitalValue.value="",
				typeofCheckIn.value="",
				carValue.value="",
				opportunityValue.value=""
			},
			onError(error) {
				let messages = error.messages || []
				for (const message of messages) {
					toast({
						title: __("Error"),
						text: message || __("{0} failed!", [actionLabel]),
						icon: "alert-circle",
						position: "bottom-center",
						iconClasses: "text-red-500",
					})
				}
			},
		}
	)
}

function getCookie(name) {
	const value = `; ${document.cookie}`
	const parts = value.split(`; ${name}=`)
	if (parts.length === 2) return parts.pop().split(";").shift()
}

async function uploadCapturedImage(checkinId, base64Image) {
	const blob = await (await fetch(base64Image)).blob()
	const formData = new FormData()

	formData.append("file", blob, `${checkinId}.jpg`)
	formData.append("doctype", "Employee Checkin")
	formData.append("docname", checkinId)
	formData.append("is_private", 1)

	// ✅ Get CSRF Token from Cookie
	const csrfToken = frappe.csrf_token || window.csrf_token || getCookie("csrf_token")

	await fetch("/api/method/upload_file", {
		method: "POST",
		body: formData,
		credentials: "include", // ✅ required to send session cookies
		headers: {
			"X-Frappe-CSRF-Token": csrfToken, // ✅ required to validate call
		},
	})
}

async function fetchLocationList() {
	const csrfToken = frappe?.csrf_token || window?.csrf_token || getCookie("csrf_token")

	const response = await fetch(
		"/api/method/hrms.api.location_api.get_all_locations",
		{
			method: "GET",
			credentials: "include", // ✅ needed to send session cookies
			headers: {
				"Content-Type": "application/json",
				"X-Frappe-CSRF-Token": csrfToken, // ✅ required
			},
		}
	)

	const result = await response.json()
		
	if (result.message.data) {
		 locations.value=result.message.data
		 console.log("Location",locations.value);
	} else {
		console.error("Error:", result.message)
		return []
	}
}

async function fetchOptions(docType) {
  const csrfToken = frappe?.csrf_token || window?.csrf_token || getCookie("csrf_token");
  const endpoint = `/api/method/hrms.api.api.get_all_${docType.toLowerCase()}`;

  const response = await fetch(endpoint, {
    method: "GET",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      "X-Frappe-CSRF-Token": csrfToken,
    },
  });

  const result = await response.json();
  return result?.message?.data || result?.data || [];
}
async function loadAllOptions() {
const leadData = await fetchOptions("lead");
const leadArray = Array.isArray(leadData) ? leadData : Object.values(leadData);

leadOptions.value = leadArray.map(i => {
  // Build label parts dynamically
  let extras = [];

  if (i.lead_name) extras.push(i.lead_name);
  if (i.mobile_no) extras.push(i.mobile_no);

  return {
    label: extras.length ? `${i.name} (${extras.join(", ")})` : i.name,
    value: i.name
  };
});
// console.log("Lead",leadOptions.value);
leadOptions.value = [
  ...leadOptions.value,
  { label: "+ Create New Lead", value: "create_new_lead" }
];

  const oppData = await fetchOptions("opportunity");
const oppArray = Array.isArray(oppData) ? oppData : Object.values(oppData);

OpportunityOptions.value = oppArray.map(i => {
  let extras = [];

  if (i.opportunity_from) extras.push(i.opportunity_from);
//   if (i.party_name) extras.push(i.party_name);
  if (i.title) extras.push(i.title);

  return {
    label: extras.length ? `${i.name} (${extras.join(", ")})` : i.name,
    value: i.name
  };
});

OpportunityOptions.value = [
  ...OpportunityOptions.value,
  { label: "+ Create New Opportunity", value: "create_new_opportunity" }
];

const hospitalData = await fetchOptions("hospital");
const hospitalArray = Array.isArray(hospitalData) ? hospitalData : Object.values(hospitalData);


HospitalOptions.value = hospitalArray.map(i => {
  let extras = [];

  // REPLACE WITH YOUR ACTUAL FIELD NAME FOR DISPLAY
  // if (i.hospital) extras.push(i.hospital);
  if (i.title) extras.push(i.title);


  return {
    label: extras.length ? `${i.name} (${extras.join(", ")})` : i.name,
    value: i.name
  };
});

// HospitalOptions.value = [
//   ...HospitalOptions.value,
//   { label: "+ Create New Hospital", value: "create_new_hospital" }
// ];

const carData = await fetchOptions("car");
const carArray = Array.isArray(carData) ? carData : Object.values(carData);

CarOptions.value = carArray.map(i => {
  let extras = [];

  // REPLACE WITH YOUR ACTUAL FIELD NAME FOR DISPLAY
  // if (i.title) extras.push(i.title);

  return {
    label: extras.length ? `${i.name} (${extras.join(", ")})` : i.name,
    value: i.name
  };
});

await fetchLocationList();

}

watch(leadValue, (val) => {
  if (val && val.value === "create_new_lead") {
    // console.log("Triggered ✅");
    showLeadModal.value = true;
    leadValue.value = null; // Reset selection
  }
});
watch(opportunityValue, (val) => {
  if (val && val.value === "create_new_opportunity") {
    // console.log("Triggered ✅ Opportunity Modal Open");
    showOpportunityModal.value = true;
    opportunityValue.value = ""; // reset
  }
});

watch(hospitalValue, (val) => {
  if (val && val.value === "create_new_hospital") {
    // console.log("Triggered ✅ Hospital Modal Open");
    showHospitalModal.value = true;
    hospitalValue.value = ""; // reset
  }
});

async function getDeviceId() {
  let deviceId = localStorage.getItem("hrms_device_id");

  if (deviceId) return deviceId;

  const fp = await FingerprintJS.load();
  const result = await fp.get();
  deviceId = result.visitorId;

  localStorage.setItem("hrms_device_id", deviceId);
  return deviceId;
}

onMounted(async () => {
	
	setTimeout(() => {
    loadAllOptions();
  }, 1000);

  const deviceId = await getDeviceId();
  device_id.value=deviceId;
// console.log(" Device ID:", deviceId);

	// Load all
  
//   console.log("Lead:", leadOptions.value);
//   console.log("Opportunity:", OpportunityOptions.value);
//   console.log("Hospital:", HospitalOptions.value);
//   console.log("CAR:", CarOptions.value);

	field_employee.value=employee.data.field_employee;
	// console.log("Employee",field_employee.value);
	socket.emit("doctype_subscribe", DOCTYPE)
	socket.on("list_update", (data) => {
		if (data.doctype == DOCTYPE) checkins.reload()
	})
})

onBeforeUnmount(() => {
	stopCamera()
	socket.emit("doctype_unsubscribe", DOCTYPE)
	socket.off("list_update")
})
</script>

<style scoped>



.custom-center-modal::part(content) {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.3);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;
}

.popup-overlay {
  position: fixed;
  inset: 0;
  background-color: rgba(0,0,0,0.45);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;
}

.popup-container {
  background: white;
  width: 450px;
  max-width: 90%;
  border-radius: 12px;
  padding: 18px;
  box-shadow: 0 6px 20px rgba(0,0,0,0.15);
  animation: fadeUp 0.25s ease;
}

@keyframes fadeUp {
  from { transform: translateY(20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

.popup-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.close-btn {
  background: none;
  border: none;
  font-size: 22px;
  cursor: pointer;
  line-height: 1;
}

.popup-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 16px;
}

.btn-cancel {
  padding: 6px 14px;
  border-radius: 6px;
  border: 1px solid #999;
  background: white;
  cursor: pointer;
}

.btn-save {
  padding: 6px 14px;
  border-radius: 6px;
  background: #2563eb;
  color: white;
  cursor: pointer;
}

</style>