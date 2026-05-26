<template>
  <!-- SNTP -->
  <div
    v-if="visible"
    class="relative col-span-full xl:col-span-3 flex flex-col bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700/60 shadow-sm rounded-b-lg"
  >
    <div
      class="absolute top-0 left-0 right-0 h-0.5 bg-pink-500"
      aria-hidden="true"
    ></div>
    <div class="px-5 py-3 border-b border-gray-200 dark:border-gray-700/60">
      <header class="flex items-center">
        <div class="w-6 h-6 rounded-full shrink-0 bg-pink-500 mr-3">
          <svg
            class="w-6 h-6 fill-current text-white"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
          >
            <circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="2" fill="none" />
            <path d="M12 7v5l3 2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
            <path d="M16 3h5v5m-5 8h5v5m-18 0h-5v-5m5-8H3V3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </div>
        <h3 class="text-lg text-gray-800 dark:text-gray-100 font-semibold">SNTP</h3>
      </header>
    </div>
    <div class="px-4 py-3">
      <div class="flex items-center gap-2">
        <label class="block text-sm font-medium shrink-0">Host</label>
        <input
          v-model="inputDict.sntpInfo.host"
          class="form-input flex-1 min-w-0"
          type="text"
          maxlength="20"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { inject, computed } from "vue";

const inputDict = inject("inputDict");

const visible = computed(
  () =>
    inputDict.value.useFuction?.sntp === 1 ||
    inputDict.value.useFuction?.sntp === true
);
</script>
