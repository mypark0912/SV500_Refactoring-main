<template>
  <!-- SNTP -->
  <div
    v-if="showSNTP"
    class="relative col-span-full xl:col-span-3 flex flex-col bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700/60 shadow-sm rounded-b-lg"
  >
    <div
      class="absolute top-0 left-0 right-0 h-0.5 bg-pink-500"
      aria-hidden="true"
    ></div>
    <div
      class="px-5 py-3 border-b border-gray-200 dark:border-gray-700/60"
    >
      <header class="flex items-center">
        <div class="w-6 h-6 rounded-full shrink-0 bg-pink-500 mr-3">
          <svg
            class="w-6 h-6 fill-current text-white"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
          >
            <!-- 시계 원형 -->
            <circle
              cx="12"
              cy="12"
              r="9"
              stroke="currentColor"
              stroke-width="2"
              fill="none"
            />

            <!-- 시계 바늘 -->
            <path
              d="M12 7v5l3 2"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            />

            <!-- 동기화 화살표 (네트워크 동기화 개념) -->
            <path
              d="M16 3h5v5m-5 8h5v5m-18 0h-5v-5m5-8H3V3"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
        </div>
        <h3 class="text-lg text-gray-800 dark:text-gray-100 font-semibold">
          SNTP
        </h3>
      </header>
    </div>
    <div class="px-4 py-3 space-y-4">
   
      <!-- <div
        class="sm:flex sm:items-center space-y-3 sm:space-y-0 sm:space-x-3 mt-4"
      >
     
        <div class="sm:w-1/2">
          <label class="block text-sm font-medium mb-2" for="fw-version"
            >Date</label
          >
       
          <flat-pickr
            v-model="inputDict.sntpInfo.date"
            :config="{ ...dateConfig, clickOpens: false }"
            class="form-input w-full p-2 border border-gray-300 rounded-md text-gray-700"
            readonly
          />
        </div>

        <div class="sm:w-1/2">
          <label class="block text-sm font-medium mb-2" for="build-date"
            >Time</label
          >
       
          <input
            v-model="inputDict.sntpInfo.time"
            class="form-input w-full p-2 border border-gray-300 rounded-md text-gray-700 cursor-pointer"
            type="time"
            step="1"
            @focus="triggerTimePicker"
            readonly
          />
        </div>
      </div> -->

      <div>
        <label class="block text-sm font-medium mb-1.5" for="rtu-id"
          >Host</label
        >
        <input
          v-model="inputDict.sntpInfo.host"
          class="form-input w-full"
          type="text"
          maxlength="20"
        />
      </div>

      <!-- <div>
        <label class="block text-sm font-medium mb-1.5" for="rtu-id"
          >Period</label
        >
        <input
          v-model="inputDict.sntpInfo.period"
          class="form-input w-full"
          type="text"
        />
      </div> -->

    </div>
  </div>
</template>
<script setup>
import { inject } from "vue";
import flatPickr from "vue-flatpickr-component";
import "flatpickr/dist/flatpickr.css";

const inputDict = inject("inputDict");

defineProps({
  showSNTP: {
    type: Boolean,
    required: true,
  },
});

const dateConfig = {
      dateFormat: "Y-m-d", // YYYY-MM-DD 포맷
      defaultDate: new Date(), // 기본값
      onChange: (selectedDates, dateStr) => {
        console.log("Selected Date:", dateStr);
      },
    };
</script>
